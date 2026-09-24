"""Publish one locally reviewed draft by merging only its validated article PR."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from create_pr import GitHub, create_pr
from engine import init_db, validate_saved_draft


def _graphql(token: str, query: str, variables: dict) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "mkrting-editorial-dashboard/0.1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub could not mark PR ready for review (HTTP {error.code})") from None
    if body.get("errors"):
        raise RuntimeError("GitHub could not mark PR ready for review: " + str(body["errors"][0].get("message", "unknown error"))[:200])
    return body["data"]


def publish_draft(draft_path: Path, progress: Callable[[str], None] | None = None) -> str:
    progress = progress or (lambda message: None)
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    article = payload["article"]
    errors = validate_saved_draft(payload)
    if errors:
        raise RuntimeError("Draft validation failed: " + "; ".join(errors))
    if payload.get("review_status") == "merged":
        return payload.get("pr_url", "Already merged")
    owner, repo, token = (os.getenv(name) for name in ("GITHUB_OWNER", "GITHUB_REPO", "GITHUB_TOKEN"))
    if not all((owner, repo, token)):
        raise RuntimeError("GitHub owner, repo or token is missing from the private .env file")
    progress("Creating or finding the article PR")
    if not payload.get("pr_url"):
        create_pr(draft_path)
        payload = json.loads(draft_path.read_text(encoding="utf-8"))
    number = int(payload["pr_number"])
    api = GitHub(owner, repo, token)
    pr = api.call("GET", f"/pulls/{number}")
    if pr.get("merged"):
        payload["review_status"] = "merged"
        payload["merged_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        draft_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return pr["html_url"]
    if pr["state"] != "open" or pr["base"]["ref"] != os.getenv("GITHUB_BASE_BRANCH", "main"):
        raise RuntimeError("PR is closed or targets a different production branch")
    if pr["head"]["repo"]["full_name"].lower() != f"{owner}/{repo}".lower():
        raise RuntimeError("PR branch belongs to a different repository")
    relative = f"content/articles/{article['slug']}.json"
    files = api.call("GET", f"/pulls/{number}/files?per_page=100")
    if len(files) != 1 or files[0]["filename"] != relative or files[0]["status"] != "added":
        raise RuntimeError("PR must add exactly this one article file")
    head_sha = pr["head"]["sha"]
    remote = api.call("GET", f"/contents/{relative}?ref={head_sha}")
    remote_article = json.loads(base64.b64decode(remote["content"]).decode("utf-8"))
    if remote_article != article:
        raise RuntimeError("PR article differs from the draft reviewed in this dashboard")
    if pr.get("draft"):
        progress("Marking the reviewed PR ready")
        _graphql(token,
                 "mutation($id:ID!){markPullRequestReadyForReview(input:{pullRequestId:$id}){pullRequest{id isDraft}}}",
                 {"id": pr["node_id"]})
    progress("Waiting for GitHub site checks")
    deadline = time.monotonic() + 240
    while True:
        checks = api.call("GET", f"/commits/{head_sha}/check-runs?per_page=100")
        build = [item for item in checks.get("check_runs", []) if item.get("name") == "build" and item.get("app", {}).get("slug") == "github-actions"]
        if build and any(item.get("status") == "completed" and item.get("conclusion") != "success" for item in build):
            raise RuntimeError("GitHub site build failed; PR remains open for review")
        if build and all(item.get("status") == "completed" and item.get("conclusion") == "success" for item in build):
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("GitHub site check is still pending; PR remains open. Try Publish again after it passes")
        time.sleep(10)
    pr = api.call("GET", f"/pulls/{number}")
    if pr["head"]["sha"] != head_sha or pr.get("mergeable") is not True:
        raise RuntimeError("PR changed or is not mergeable; review it on GitHub")
    progress("Merging the reviewed article PR")
    merged = api.call("PUT", f"/pulls/{number}/merge", {"sha": head_sha, "merge_method": "squash", "commit_title": f"Publish: {article['title']}"})
    if not merged.get("merged"):
        raise RuntimeError("GitHub did not confirm the merge")
    payload["review_status"] = "merged"
    payload["merged_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    draft_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    connection = init_db()
    try:
        connection.execute("UPDATE clusters SET status='merged' WHERE id=?", (payload["cluster_id"],))
        connection.commit()
    finally:
        connection.close()
    return pr["html_url"]

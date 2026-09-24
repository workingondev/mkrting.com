"""Create one editorial GitHub PR from a locally checked draft.

The token can create an article branch and PR, but this tool never merges or
deploys. Repository rules should require a human review and passing build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from engine import ROOT, validate_saved_draft


class GitHub:
    def __init__(self, owner: str, repo: str, token: str):
        self.root = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
        self.token = token

    def call(self, method: str, path: str, body: dict | None = None, *, missing_ok: bool = False):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.root + path, data=data, method=method, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "mkrting-editorial-pr/0.1",
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if missing_ok and error.code == 404:
                return None
            raise RuntimeError(f"GitHub API {method} {path} returned HTTP {error.code}") from error


def create_pr(draft_path: Path) -> str:
    owner, repo = os.getenv("GITHUB_OWNER"), os.getenv("GITHUB_REPO")
    token, base = os.getenv("GITHUB_TOKEN"), os.getenv("GITHUB_BASE_BRANCH", "main")
    if not all((owner, repo, token)):
        raise RuntimeError("Set GITHUB_OWNER, GITHUB_REPO and GITHUB_TOKEN before creating PRs")
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    if payload.get("pr_url"):
        return payload["pr_url"]
    article = payload["article"]
    errors = validate_saved_draft(payload)
    if errors:
        raise RuntimeError("Draft failed final validation: " + "; ".join(errors))
    slug = article["slug"]
    relative = f"content/articles/{slug}.json"
    if (ROOT / relative).exists():
        raise RuntimeError(f"Article already exists locally: {relative}")
    sources = "\n".join(f"- [{item['label']}]({item['url']}) ({item['type']})" for item in article["sources"])
    research = payload["research"]
    claims = "\n".join(f"- **{claim['fact']}** — [{claim['source_url']}]({claim['source_url']}) ({claim['confidence']})" for claim in research["claims"])
    unknowns = "\n".join(f"- {question}" for question in research.get("unknowns", [])) or "- None recorded; editor should still check."
    ai_check = payload.get("ai_check_report", {})
    body = f"""## Editorial summary

{article['dek']}

**Campaign:** {article['brand']}  
**Angle:** {article['signal']}  
**Reader question:** {article['reader_question']}  
**Search title:** {article['seo_title']}  
**Startup lesson:** {article['lesson']}
**Evidence basis:** {('One attributed trade publication RSS summary; full report was not machine-readable' if payload.get('source_access') == 'rss_summary_only' else 'One attributed trade report; no official campaign page verified') if payload.get('evidence_policy') == 'reported_analysis' else 'Official campaign page and independent reporting'}

## Evidence

{sources}

## Claim ledger from AI research

{claims}

**Still unknown**

{unknowns}

**Why selected:** {research.get('strategic_angle', 'Editorial assessment required')}  
**Image rights:** {payload.get('image_rights_status', 'Not recorded; review required')}  
**AI check:** {ai_check.get('status', 'not independently verified')} — {ai_check.get('note', 'Review required')}  
**Originality:** {payload.get('originality_assessment', 'Human review required')}

## Review before merge

- [ ] Check every factual claim in the article, including claims missing from this ledger, against the linked sources.
- [ ] Confirm headline, interpretation, dates, and brand/agency credits.
- [ ] Confirm media and embed rights; no third-party creative is copied into this PR.
- [ ] Check that the article adds analysis beyond source reports.
- [ ] Check the reader question, search title, description, and visible heading against the actual article.
- [ ] Confirm the publication date and corrections route.

AI-assisted draft. Human merge required. Merging builds the public site.
"""
    api = GitHub(owner, repo, token)
    if api.call("GET", f"/contents/{relative}?ref={urllib.parse.quote(base)}", missing_ok=True):
        raise RuntimeError(f"Article already exists on {base}: {relative}")
    article_json = json.dumps(article, ensure_ascii=False, indent=2) + "\n"
    suffix = hashlib.sha256(article_json.encode()).hexdigest()[:10]
    branch = f"articles/{slug}-{suffix}"
    encoded_branch = urllib.parse.quote(branch, safe="")
    branch_ref = api.call("GET", f"/git/ref/heads/{encoded_branch}", missing_ok=True)
    if branch_ref:
        existing = api.call("GET", f"/pulls?state=open&head={urllib.parse.quote(owner + ':' + branch)}")
        if existing:
            payload["pr_url"] = existing[0]["html_url"]
            payload["pr_number"] = existing[0]["number"]
            draft_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return payload["pr_url"]
    else:
        base_ref = api.call("GET", f"/git/ref/heads/{urllib.parse.quote(base, safe='')}")
        base_sha = base_ref["object"]["sha"]
        base_commit = api.call("GET", f"/git/commits/{base_sha}")
        tree = api.call("POST", "/git/trees", {"base_tree": base_commit["tree"]["sha"], "tree": [{"path": relative, "mode": "100644", "type": "blob", "content": article_json}]})
        commit = api.call("POST", "/git/commits", {"message": f"Add campaign analysis: {article['title']}", "tree": tree["sha"], "parents": [base_sha]})
        api.call("POST", "/git/refs", {"ref": f"refs/heads/{branch}", "sha": commit["sha"]})
    pr = api.call("POST", "/pulls", {"title": f"Editorial review: {article['title']}", "head": branch, "base": base, "body": body, "draft": True})
    payload["pr_url"] = pr["html_url"]
    payload["pr_number"] = pr["number"]
    draft_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pr["html_url"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    print(create_pr(args.draft))

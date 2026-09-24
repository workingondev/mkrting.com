"""Show local editorial backend readiness without printing credentials."""

from __future__ import annotations

import json
import os
import subprocess

from engine import DB, FEEDS, LOCAL, ROOT, evidence_ready, init_db


def timer_state() -> str:
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "mkrting-cycle.timer"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unavailable"
    if "Failed to connect to bus" in result.stderr:
        return "unavailable in this session"
    return result.stdout.strip() or "unknown"


def status() -> dict:
    connection = init_db()
    try:
        clusters = connection.execute("SELECT id FROM clusters WHERE status='new'").fetchall()
        ready = 0
        for cluster in clusters:
            items = connection.execute(
                "SELECT url,is_primary FROM items WHERE cluster_id=?", (cluster["id"],)
            ).fetchall()
            ready += int(evidence_ready(items))
        latest_feeds = connection.execute(
            "SELECT f.feed_id, f.status, f.checked_at FROM feed_runs f "
            "JOIN (SELECT feed_id, MAX(id) AS last_id FROM feed_runs GROUP BY feed_id) x "
            "ON f.id=x.last_id"
        ).fetchall()
        feed_results = {row["feed_id"]: dict(row) for row in latest_feeds}
        enabled_feeds = [feed for feed in json.loads(FEEDS.read_text(encoding="utf-8")) if feed.get("enabled")]
        drafts = []
        for path in sorted((LOCAL / "drafts").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            drafts.append({"file": path.name, "pr_created": bool(payload.get("pr_url"))})
        configured = {
            "gemini_key": bool(os.getenv("GEMINI_API_KEY")),
            "github_repository": bool(os.getenv("GITHUB_OWNER") and os.getenv("GITHUB_REPO")),
            "github_token": bool(os.getenv("GITHUB_TOKEN")),
            "instagram": all(os.getenv(name) for name in ("META_ACCESS_TOKEN", "META_IG_USER_ID", "META_API_VERSION")),
        }
        next_steps = []
        if not configured["gemini_key"]:
            next_steps.append("Add GEMINI_API_KEY to the private .env file to enable research and drafts.")
        if not configured["github_repository"] or not configured["github_token"]:
            next_steps.append("Set GitHub repository and token in private .env to enable draft PRs.")
        if ready == 0:
            next_steps.append("Add a verified brand or agency campaign URL and independent reporting to one lead cluster.")
        if not enabled_feeds:
            next_steps.append("Enable at least one permitted source feed.")
        elif not any(feed_results.get(feed["id"], {}).get("status") == "ok" for feed in enabled_feeds):
            next_steps.append("Check feed health on the Linux laptop; no enabled feed succeeded on its latest recorded run.")
        timer = timer_state()
        if timer == "unavailable in this session":
            next_steps.append("Check the user timer with systemctl --user on the Linux laptop; this session cannot access it.")
        elif timer != "active":
            next_steps.append("Install or start the mkrting-cycle user timer on the Linux laptop.")
        return {
            "project": str(ROOT),
            "database_exists": DB.exists(),
            "credentials_configured": configured,
            "timer": timer,
            "leads": {
                "new_clusters": len(clusters),
                "ready_for_draft": ready,
                "waiting_for_evidence": len(clusters) - ready,
                "total_items": connection.execute("SELECT COUNT(*) FROM items").fetchone()[0],
                "verified_primary_items": connection.execute("SELECT COUNT(*) FROM items WHERE is_primary=1").fetchone()[0],
            },
            "feeds": {
                "enabled": len(enabled_feeds),
                "last_ok": sum(feed_results.get(feed["id"], {}).get("status") == "ok" for feed in enabled_feeds),
                "last_failed": sum(feed_results.get(feed["id"], {}).get("status") == "failed" for feed in enabled_feeds),
                "last_skipped": sum(feed_results.get(feed["id"], {}).get("status") == "skipped" for feed in enabled_feeds),
                "never_checked": sum(feed["id"] not in feed_results for feed in enabled_feeds),
            },
            "local_drafts": {"total": len(drafts), "awaiting_pr": sum(not draft["pr_created"] for draft in drafts)},
            "next_steps": next_steps,
        }
    finally:
        connection.close()


if __name__ == "__main__":
    print(json.dumps(status(), ensure_ascii=False, indent=2))

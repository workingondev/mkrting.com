"""Run one bounded local editorial cycle; intended for a Linux systemd timer."""

from __future__ import annotations

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from create_pr import create_pr
from engine import LOCAL, collect, draft_cluster, init_db, shortlist


def cycle() -> dict:
    connection = init_db()
    connection.execute("CREATE TABLE IF NOT EXISTS daily_activity (date_ist TEXT PRIMARY KEY, drafts INTEGER NOT NULL DEFAULT 0)")
    connection.execute("""CREATE TABLE IF NOT EXISTS draft_attempts (
        cluster_id INTEGER NOT NULL, date_ist TEXT NOT NULL, outcome TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT '', attempted_at TEXT NOT NULL,
        PRIMARY KEY(cluster_id, date_ist)
    )""")
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    connection.execute("INSERT OR IGNORE INTO daily_activity(date_ist) VALUES(?)", (today,))
    connection.commit()
    report: dict = {"date_ist": today, "rss": collect(connection), "instagram": "not configured", "leads": {}, "drafts": [], "prs": [], "held": []}

    if all(os.getenv(key) for key in ("META_ACCESS_TOKEN", "META_IG_USER_ID", "META_API_VERSION")):
        from meta_collect import collect as collect_meta
        try:
            report["instagram"] = collect_meta()
        except Exception as error:
            report["held"].append(f"Instagram: {type(error).__name__}: {error}")

    leads = shortlist(connection, 1000)
    report["leads"] = {
        "new": sum(lead["status"] == "new" for lead in leads),
        "ready_for_draft": sum(lead["status"] == "new" and lead["ready_for_draft"] for lead in leads),
    }

    if os.getenv("GEMINI_API_KEY"):
        cap = max(0, min(3, int(os.getenv("MAX_DRAFTS_PER_DAY", "3"))))
        made = connection.execute("SELECT drafts FROM daily_activity WHERE date_ist=?", (today,)).fetchone()[0]
        for lead in leads[:30]:
            if made >= cap:
                break
            if not lead["ready_for_draft"] or lead["status"] != "new":
                continue
            attempted = connection.execute("SELECT 1 FROM draft_attempts WHERE cluster_id=? AND date_ist=?", (lead["id"], today)).fetchone()
            if attempted:
                report.setdefault("retry_guard_skips", []).append(lead["id"])
                continue
            try:
                path = draft_cluster(connection, lead["id"])
            except RuntimeError as error:
                report["held"].append(f"Lead {lead['id']}: {error}")
                connection.execute("INSERT INTO draft_attempts(cluster_id,date_ist,outcome,detail,attempted_at) VALUES(?,?,?,?,?)", (lead["id"], today, "held", str(error)[:500], datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")))
                connection.commit()
                continue
            connection.execute("INSERT INTO draft_attempts(cluster_id,date_ist,outcome,detail,attempted_at) VALUES(?,?,?,?,?)", (lead["id"], today, "drafted", "", datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")))
            made += 1
            connection.execute("UPDATE daily_activity SET drafts=? WHERE date_ist=?", (made, today))
            connection.commit()
            report["drafts"].append(path.name)
    else:
        report["held"].append("GEMINI_API_KEY is empty; discovery continues but drafting is disabled")

    if report["leads"]["new"] and not report["leads"]["ready_for_draft"]:
        report["held"].append("No lead has both a verified primary campaign source and independent reporting")

    if all(os.getenv(key) for key in ("GITHUB_OWNER", "GITHUB_REPO", "GITHUB_TOKEN")):
        for draft_path in sorted((LOCAL / "drafts").glob("*.json")):
            payload = json.loads(draft_path.read_text(encoding="utf-8"))
            if payload.get("pr_url"):
                continue
            try:
                report["prs"].append(create_pr(draft_path))
            except RuntimeError as error:
                report["held"].append(f"PR {draft_path.name}: {error}")
    elif list((LOCAL / "drafts").glob("*.json")):
        report["held"].append("GitHub repository or token is missing; local drafts cannot become PRs")

    return report


if __name__ == "__main__":
    print(json.dumps(cycle(), ensure_ascii=False, indent=2))

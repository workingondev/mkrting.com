"""Collect every two hours and research a few evidence-ready leads."""

from __future__ import annotations

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from editor_lock import editorial_lock
from engine import LOCAL, collect, init_db, research_cluster, shortlist


def cycle() -> dict:
    with editorial_lock():
        connection = init_db()
        try:
            today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
            report = {"date_ist": today, "rss": collect(connection), "researched": [], "held": []}
            connection.execute("""CREATE TABLE IF NOT EXISTS background_research (
                cluster_id INTEGER NOT NULL, date_ist TEXT NOT NULL, outcome TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '', PRIMARY KEY(cluster_id, date_ist)
            )""")
            connection.commit()
            max_daily = max(0, min(8, int(os.getenv("MAX_BACKGROUND_RESEARCH_PER_DAY", "4"))))
            attempted_today = connection.execute("SELECT COUNT(*) FROM background_research WHERE date_ist=?", (today,)).fetchone()[0]
            if not os.getenv("GEMINI_API_KEY"):
                report["held"].append("Gemini key missing; leads were still collected")
            elif attempted_today < max_daily:
                for lead in shortlist(connection, 30):
                    if len(report["researched"]) + len(report["held"]) >= 2 or attempted_today >= max_daily:
                        break
                    if lead["status"] != "new" or not lead["ready_for_draft"]:
                        continue
                    if connection.execute("SELECT 1 FROM background_research WHERE cluster_id=? AND date_ist=?", (lead["id"], today)).fetchone():
                        continue
                    try:
                        research, _, _, _, _ = research_cluster(connection, lead["id"])
                        outcome, detail = "ready", research.get("strategic_angle", "")[:240]
                        report["researched"].append({"id": lead["id"], "angle": detail})
                    except (RuntimeError, TimeoutError, OSError) as error:
                        outcome, detail = "held", str(error)[:300]
                        report["held"].append(f"Lead {lead['id']}: {detail}")
                    connection.execute("INSERT OR REPLACE INTO background_research(cluster_id,date_ist,outcome,detail) VALUES(?,?,?,?)", (lead["id"], today, outcome, detail))
                    connection.commit()
                    attempted_today += 1
            (LOCAL / "last_collect.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return report
        finally:
            connection.close()


if __name__ == "__main__":
    print(json.dumps(cycle(), ensure_ascii=False, indent=2))

"""Optional Instagram Business Discovery collector for verified professional accounts.

Requires approved Meta access. It never logs tokens, downloads media, or uses
Instagram's private web endpoints. A watchlist row is enabled only after its
handle is verified against an official website.
"""

from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from engine import ROOT, add_item, init_db, interesting

WATCHLIST = ROOT / "data" / "instagram_watchlist.csv"


def configured() -> tuple[str, str, str]:
    token = os.getenv("META_ACCESS_TOKEN", "")
    ig_user = os.getenv("META_IG_USER_ID", "")
    version = os.getenv("META_API_VERSION", "")
    if not all((token, ig_user, version)):
        raise RuntimeError("Set META_ACCESS_TOKEN, META_IG_USER_ID and META_API_VERSION after Meta access is approved")
    if not version.startswith("v") or not version[1:].replace(".", "").isdigit():
        raise ValueError("META_API_VERSION must look like v24.0")
    return token, ig_user, version


def get_media(handle: str, token: str, ig_user: str, version: str) -> list[dict]:
    fields = f"business_discovery.username({handle}){{id,username,media.limit(5){{id,caption,permalink,timestamp}}}}"
    url = f"https://graph.facebook.com/{version}/{ig_user}?{urllib.parse.urlencode({'fields': fields})}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "mkrting-research/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.load(response)
    return body.get("business_discovery", {}).get("media", {}).get("data", [])


def collect(limit: int = 20, pause: float = 1.0) -> dict[str, int]:
    token, ig_user, version = configured()
    with WATCHLIST.open(newline="", encoding="utf-8") as file:
        accounts = [row for row in csv.DictReader(file) if row["status"] == "verified" and row["instagram_handle"]]
    connection = init_db()
    connection.execute("CREATE TABLE IF NOT EXISTS meta_state (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
    position = connection.execute("SELECT value FROM meta_state WHERE key='watchlist_position'").fetchone()
    start = position[0] if position else 0
    selected = [accounts[(start + index) % len(accounts)] for index in range(min(limit, len(accounts)))] if accounts else []
    counts = {"checked_accounts": 0, "new_posts": 0, "failed_accounts": 0}
    for row in selected:
        try:
            posts = get_media(row["instagram_handle"], token, ig_user, version)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"Instagram account {row['name']}: {type(error).__name__} (held)")
            counts["failed_accounts"] += 1
            time.sleep(pause)
            continue
        counts["checked_accounts"] += 1
        for post in posts:
            caption = " ".join((post.get("caption") or "").split())
            permalink = post.get("permalink", "")
            if not permalink or not caption or not interesting(caption[:180], ""):
                continue
            title = caption[:140].rsplit(" ", 1)[0] or caption[:140]
            source_type = "official_instagram" if row["category"] in {"Brand", "D2C brand", "India agency", "Global agency"} else "curator_instagram"
            _, created = add_item(connection, url=permalink, title=title, summary=caption[:600], source_name=row["name"], source_type=source_type, region="India" if row["category"] in {"India publisher", "India agency", "Brand", "D2C brand"} else "Global", published_at=post.get("timestamp", ""), is_primary=source_type == "official_instagram")
            counts["new_posts"] += int(created)
        time.sleep(pause)
    if accounts:
        connection.execute("INSERT INTO meta_state(key,value) VALUES('watchlist_position',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ((start + len(selected)) % len(accounts),))
        connection.commit()
    return counts


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))

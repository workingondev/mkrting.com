"""Audit official website links for Instagram handles without scraping Instagram.

This deliberately fetches only the organization's own homepage, after robots
checks. A discovered link is a suggestion; an editor should still confirm the
regional account and whether the page is useful for campaign discovery.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "data" / "instagram_watchlist.csv"
USER_AGENT = "mkrting-research/0.1 (+https://mkrting.com/about/)"
HANDLE_RE = re.compile(r"(?:https?:)?(?:\\?/\\?/|//)(?:www\.)?instagram\.com/([A-Za-z0-9._]+)", re.I)
IGNORE = {"p", "reel", "reels", "stories", "explore", "accounts", "tv", "about", "developer", "embed.js"}


def get(url: str, limit: int = 750_000) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=9) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("response too large")
        return response.status, data.decode("utf-8", "replace")


def allowed(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        status, body = get(robots_url, 300_000)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return True, "robots.txt absent"
        return False, f"robots.txt HTTP {error.code}"
    except Exception as error:  # fail closed if robots cannot be read
        return False, f"robots.txt unavailable: {type(error).__name__}"
    if status != 200:
        return False, f"robots.txt HTTP {status}"
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.splitlines())
    return parser.can_fetch(USER_AGENT, url), "robots.txt checked"


def audit(row: dict[str, str]) -> dict[str, object]:
    name, website = row["name"], row["website"]
    permitted, reason = allowed(website)
    if not permitted:
        return {"name": name, "website": website, "status": "skipped", "reason": reason, "handles": []}
    try:
        status, html = get(website)
    except Exception as error:
        return {"name": name, "website": website, "status": "error", "reason": f"{type(error).__name__}: {str(error)[:90]}", "handles": []}
    normalized = html.replace("\\/", "/").replace("&amp;", "&")
    handles = sorted({m.group(1).rstrip(".") for m in HANDLE_RE.finditer(normalized) if m.group(1).lower() not in IGNORE})
    return {"name": name, "website": website, "status": "found" if handles else "no_link", "reason": f"HTTP {status}; {reason}", "handles": handles}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "instagram_audit.json")
    args = parser.parse_args()
    with WATCHLIST.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))[: args.limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(audit, rows))
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {status: sum(item["status"] == status for item in results) for status in ("found", "no_link", "skipped", "error")}
    print(f"Audited {len(results)} websites: {counts}. Review {args.output}")


if __name__ == "__main__":
    main()

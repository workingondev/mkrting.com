"""Check held RSS URLs on the connected Linux laptop before activation.

Usage: python3 tools/probe_feeds.py
       python3 tools/probe_feeds.py --activate
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from engine import USER_AGENT, allowed, feed_entries, interesting

FEEDS = Path(__file__).resolve().parents[1] / "data/feeds.json"


def check(feed):
    url = feed["url"]
    permitted, reason = allowed(url)
    if not permitted:
        return {"id": feed["id"], "status": "held", "reason": reason}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml"})
        with urllib.request.urlopen(request, timeout=15) as response:
            final_url = response.url
            content_type = response.headers.get_content_type()
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("feed over 2 MB")
        if urlparse(final_url).hostname.removeprefix("www.") != urlparse(url).hostname.removeprefix("www."):
            raise ValueError("redirected to another domain")
        if content_type not in {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml", "text/plain"}:
            raise ValueError(f"unexpected content type: {content_type}")
        entries = feed_entries(data.decode("utf-8-sig", "replace"))
        if not entries or not any(e["title"] and e["link"] for e in entries):
            raise ValueError("no usable RSS/Atom entries")
        relevant = sum(bool(e["title"] and interesting(e["title"], e["summary"])) for e in entries[:100])
        return {"id": feed["id"], "status": "passed", "entries": len(entries), "relevant": relevant, "content_type": content_type}
    except Exception as error:
        return {"id": feed["id"], "status": "held", "reason": f"{type(error).__name__}: {str(error)[:180]}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activate", action="store_true", help="enable passing feeds with at least one relevant item")
    args = parser.parse_args()
    feeds = json.loads(FEEDS.read_text())
    results = []
    for feed in feeds:
        if feed["enabled"]:
            continue
        result = check(feed)
        results.append(result)
        if args.activate and result["status"] == "passed" and result["relevant"] > 0:
            feed["enabled"] = True
            feed["proof"] = f"Linux probe passed: {result['entries']} entries, {result['relevant']} relevant; content type {result['content_type']}"
        print(json.dumps(result), flush=True)
    if args.activate:
        FEEDS.write_text(json.dumps(feeds, ensure_ascii=False, indent=2) + "\n")
        from build_source_registry import main as rebuild_sources
        rebuild_sources()
    print(json.dumps({"checked": len(results), "passed": sum(r["status"] == "passed" for r in results), "active_total": sum(f["enabled"] for f in feeds)}), file=sys.stderr)


if __name__ == "__main__":
    main()

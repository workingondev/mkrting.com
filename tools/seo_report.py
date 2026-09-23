"""Turn Google Search Console CSV exports into an editorial review list."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def number(value: str) -> float:
    return float(value.strip().replace(",", "").replace("%", ""))


def rows(path: Path, name_candidates: tuple[str, ...]) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fields = {field.lower().strip(): field for field in (reader.fieldnames or [])}
        dimension = next((fields[candidate] for candidate in name_candidates if candidate in fields), None)
        if not dimension or not all(field in fields for field in ("clicks", "impressions", "ctr", "position")):
            raise ValueError(f"{path}: expected a Search Console table with dimension, Clicks, Impressions, CTR and Position")
        result = []
        for row in reader:
            try:
                result.append({"name": row[dimension].strip(), "clicks": int(number(row[fields["clicks"]])), "impressions": int(number(row[fields["impressions"]])), "ctr": number(row[fields["ctr"]]), "position": number(row[fields["position"]])})
            except (ValueError, KeyError):
                continue
    return result


def report(queries: list[dict], pages: list[dict]) -> str:
    lines = ["# mkrting.com search review", "", "Search Console data describes what appeared in Google Search. Inspect the actual query and page before changing content; average position and CTR vary by country, device and result type.", ""]
    opportunities = sorted((row for row in queries if row["impressions"] >= 50 and 4 <= row["position"] <= 20), key=lambda row: (-row["impressions"], row["position"]))[:15]
    lines.extend(["## Queries to inspect", "", "| Query | Impressions | Clicks | CTR | Avg. position |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in opportunities:
        lines.append(f"| {row['name'].replace('|', '/')} | {row['impressions']} | {row['clicks']} | {row['ctr']:.1f}% | {row['position']:.1f} |")
    if not opportunities:
        lines.append("| No query has enough data yet | — | — | — | — |")
    lines.extend(["", "Review each query's search intent and the ranking page. Improve missing answers, source detail, headline clarity or internal links when the page genuinely benefits.", "", "## Pages with visibility", "", "| Page | Impressions | Clicks | CTR | Avg. position |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in sorted(pages, key=lambda item: -item["impressions"])[:15]:
        lines.append(f"| {row['name'].replace('|', '/')} | {row['impressions']} | {row['clicks']} | {row['ctr']:.1f}% | {row['position']:.1f} |")
    if not pages:
        lines.append("| No page data supplied | — | — | — | — |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True, help="Search Console Queries CSV export")
    parser.add_argument("--pages", type=Path, required=True, help="Search Console Pages CSV export")
    parser.add_argument("--output", type=Path, default=Path(".local/seo-report.md"))
    args = parser.parse_args()
    content = report(rows(args.queries, ("top queries", "queries", "query")), rows(args.pages, ("top pages", "pages", "page")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

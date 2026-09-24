"""Check crawlable pages, search metadata, internal navigation and feeds."""

from __future__ import annotations

import sys
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from build_site import BASE_URL

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.canonical: list[str] = []
        self.title = ""
        self.descriptions: list[str] = []
        self.h1_count = 0
        self.images: list[tuple[str, str | None]] = []
        self.schemas: list[dict] = []
        self.in_title = False
        self.in_schema = False
        self.schema_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonical.append(attributes.get("href") or "")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "meta" and attributes.get("name") == "description":
            self.descriptions.append(attributes.get("content") or "")
        if tag == "img":
            self.images.append((attributes.get("src") or "", attributes.get("alt")))
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self.in_schema = True
            self.schema_text = ""

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.in_schema:
            self.schema_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_schema:
            self.in_schema = False
            try:
                self.schemas.append(json.loads(self.schema_text))
            except json.JSONDecodeError:
                self.schemas.append({"invalid": True})


def main() -> None:
    errors: list[str] = []
    pages = list(DIST.rglob("*.html"))
    if not pages:
        raise SystemExit("No site pages were built")
    titles: dict[str, Path] = {}
    descriptions: dict[str, Path] = {}
    canonical_urls: set[str] = set()
    for page in pages:
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        relative = page.relative_to(DIST)
        path = "/" if relative.as_posix() == "index.html" else "/" + relative.parent.as_posix() + "/"
        expected = BASE_URL + path
        if parser.canonical != [expected]:
            errors.append(f"{relative}: canonical does not match its public path")
        else:
            canonical_urls.add(expected)
        if not parser.title.strip() or parser.title in titles:
            errors.append(f"{relative}: missing or duplicate title")
        else:
            titles[parser.title] = relative
        if len(parser.descriptions) != 1 or len(parser.descriptions[0]) < 60:
            errors.append(f"{relative}: missing or thin description")
        elif parser.descriptions[0] in descriptions:
            errors.append(f"{relative}: duplicate description")
        else:
            descriptions[parser.descriptions[0]] = relative
        if parser.h1_count != 1:
            errors.append(f"{relative}: expected one main heading")
        for src, alt in parser.images:
            # alt="" is valid for decorative artwork beside an article title.
            if alt is None:
                errors.append(f"{relative}: image lacks alternative text")
            if src.startswith("/") and not (DIST / src.lstrip("/")).is_file():
                errors.append(f"{relative}: missing image {src}")
        needs_schema = path == "/" or (path.startswith("/campaigns/") and path != "/campaigns/") or (path.startswith("/guides/") and path != "/guides/")
        if any(schema.get("invalid") for schema in parser.schemas) or (needs_schema and not parser.schemas):
            errors.append(f"{relative}: missing or invalid structured data")
        elif needs_schema:
            types = {node.get("@type") for schema in parser.schemas for node in schema.get("@graph", [schema])}
            required = {"WebSite"} if path == "/" else {"Article", "BreadcrumbList"}
            if not required.issubset(types):
                errors.append(f"{relative}: incomplete structured data")
        for link in parser.links:
            if not link.startswith("/"):
                continue
            pathname = urlsplit(link).path
            target = DIST / pathname.lstrip("/")
            if pathname.endswith("/"):
                target /= "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(DIST)}: broken {link}")
    for name in ("sitemap.xml", "rss.xml"):
        try:
            ET.parse(DIST / name)
        except (FileNotFoundError, ET.ParseError) as error:
            errors.append(f"{name}: {error}")
    try:
        sitemap_urls = {element.text for element in ET.parse(DIST / "sitemap.xml").iter() if element.tag.endswith("}loc")}
        if sitemap_urls != canonical_urls:
            errors.append("sitemap URLs do not match canonical HTML pages")
    except (FileNotFoundError, ET.ParseError):
        pass
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"Checked {len(pages)} pages, search metadata, internal links, sitemap and RSS")


if __name__ == "__main__":
    main()

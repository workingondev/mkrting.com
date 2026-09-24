"""Find campaign evidence linked by reporting, then create a sourced AI draft."""

from __future__ import annotations

import html
import re
import urllib.parse
from html.parser import HTMLParser

from engine import add_item, clean_url, draft_cluster, draft_from_report, evidence_ready, get_cluster, primary_url_specific, source_text
from verify_instagram import allowed, get


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.label: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data):
        if self.href:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(self.label)))
            self.href = None
            self.label = []


def brand_terms(title: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    skip = {"how", "why", "the", "new", "a", "an", "india", "indian", "for", "of", "to", "in", "on", "by", "with", "from", "and", "campaign", "marketing", "advertising", "brand", "launches", "launch", "reveals", "unveils", "video", "film", "ad", "ads"}
    return [word for word in words if word not in skip and len(word) > 2][:3]


def linked_official_candidates(items, title: str) -> list[tuple[str, str]]:
    terms = brand_terms(title)
    if not terms:
        return []
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in items[:3]:
        if item["is_primary"] or not allowed(item["url"])[0]:
            continue
        try:
            _, page = get(item["url"], 750_000)
        except (OSError, ValueError):
            continue
        parser = Links()
        parser.feed(page)
        for href, label in parser.links:
            url = urllib.parse.urljoin(item["url"], html.unescape(href))
            try:
                url = clean_url(url)
            except ValueError:
                continue
            host = urllib.parse.urlparse(url).hostname or ""
            source_host = urllib.parse.urlparse(item["url"]).hostname or ""
            if (url in seen or host == source_host or not primary_url_specific(url)
                    or not any(term in host.replace("-", "") for term in terms)):
                continue
            seen.add(url)
            found.append((url, label.strip()[:160]))
            if len(found) >= 12:
                return found
    return found


def brand_site_candidates(title: str) -> list[tuple[str, str]]:
    """Inspect likely brand-owned websites and their public sitemaps, without AI search."""
    import xml.etree.ElementTree as ET

    brand = brand_terms(title)[0] if brand_terms(title) else ""
    if not brand or len(brand) < 4:
        return []
    title_words = {word for word in re.findall(r"[a-z0-9]+", title.lower())
                   if len(word) >= 4 and word not in {"campaign", "brand", "advertising", "marketing", "latest", "launches"}}
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for domain in (f"{brand}.com", f"{brand}.in", f"{brand}.co.in"):
        home = f"https://www.{domain}/"
        if not allowed(home)[0]:
            continue
        try:
            _, page = get(home, 500_000)
            links = Links()
            links.feed(page)
        except (OSError, ValueError):
            continue
        for href, label in links.links:
            url = urllib.parse.urljoin(home, html.unescape(href))
            host = urllib.parse.urlparse(url).hostname or ""
            if not host.endswith(domain) or not primary_url_specific(url):
                continue
            words = set(re.findall(r"[a-z0-9]+", (url + " " + label).lower()))
            if len(words & title_words) >= 2:
                try:
                    clean = clean_url(url)
                except ValueError:
                    continue
                if clean not in seen:
                    seen.add(clean)
                    found.append((clean, label.strip()[:160]))
        sitemap = f"https://www.{domain}/sitemap.xml"
        urls = []
        pending = [sitemap]
        inspected = 0
        while pending and inspected < 4:
            sitemap_url = pending.pop(0)
            if not allowed(sitemap_url)[0]:
                continue
            inspected += 1
            try:
                _, xml = get(sitemap_url, 1_500_000)
                root = ET.fromstring(xml)
            except (OSError, ValueError, ET.ParseError):
                continue
            locations = [element.text.strip() for element in root.iter()
                         if element.tag.rsplit('}', 1)[-1] == 'loc' and element.text]
            if root.tag.rsplit('}', 1)[-1] == 'sitemapindex':
                preferred = [url for url in locations if any(term in url.lower() for term in
                             ('blog', 'post', 'news', 'press', 'article', 'campaign'))]
                pending.extend((preferred or locations)[:3])
            else:
                urls.extend(locations[:1500])
        for url in urls[:1500]:
            host = urllib.parse.urlparse(url).hostname or ""
            if not host.endswith(domain) or not primary_url_specific(url):
                continue
            words = set(re.findall(r"[a-z0-9]+", urllib.parse.urlparse(url).path.lower()))
            if len(words & title_words) >= 2:
                try:
                    clean = clean_url(url)
                except ValueError:
                    continue
                if clean not in seen:
                    seen.add(clean)
                    found.append((clean, "Brand website sitemap"))
            if len(found) >= 12:
                break
    return found[:12]


def discover_primary(connection, cluster_id: int) -> str | None:
    cluster, items = get_cluster(connection, cluster_id)
    if evidence_ready(items):
        return next(item["url"] for item in items if item["is_primary"])
    title_words = {word for word in re.findall(r"[a-z0-9]+", cluster["title"].lower())
                   if len(word) >= 4 and word not in {"campaign", "brand", "launches", "latest", "brings", "india", "marketing", "advertising"}}
    for candidates in (linked_official_candidates(items, cluster["title"]), brand_site_candidates(cluster["title"])):
        for url, label in candidates:
            host = urllib.parse.urlparse(url).hostname or ""
            host_key = host.removeprefix("www.").split(".")[0].replace("-", "")
            if not any(term in host_key for term in brand_terms(cluster["title"])):
                continue
            body, status = source_text(url)
            if not body:
                continue
            page_words = set(re.findall(r"[a-z0-9]+", (label + " " + body[:5000]).lower()))
            if len(title_words & page_words) < 2:
                continue
            _, created = add_item(connection, cluster_id=cluster_id, url=url,
                                  title=f"Official campaign page: {cluster['title']}",
                                  summary=f"Campaign-specific page on {host}; inspected for matching story details.",
                                  source_name=host_key, source_type="primary", region="India", is_primary=True)
            if created:
                return url
    return None


def create_selected_draft(connection, cluster_id: int, progress):
    progress("Finding and checking original campaign evidence")
    _, items = get_cluster(connection, cluster_id)
    if not evidence_ready(items):
        discover_primary(connection, cluster_id)
    _, items = get_cluster(connection, cluster_id)
    if not evidence_ready(items):
        progress("Official page not found; researching the collected report and writing a clearly attributed draft")
        return draft_from_report(connection, cluster_id)
    progress("Researching evidence and writing the article with Gemini")
    return draft_cluster(connection, cluster_id)

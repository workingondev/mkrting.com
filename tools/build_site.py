"""Build the public, static mkrting.com site from reviewed article JSON files."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "articles"
GUIDES = ROOT / "content" / "guides"
DIST = ROOT / "dist"
ASSETS = ROOT / "site" / "assets"
# Vercel redirects www to the apex domain. Keep every generated search signal
# on that same destination, even if a legacy Vercel SITE_URL still says www.
CANONICAL_ORIGIN = "https://mkrting.com"
configured_origin = os.getenv("SITE_URL", CANONICAL_ORIGIN).rstrip("/")
if configured_origin not in {CANONICAL_ORIGIN, "https://www.mkrting.com"}:
    raise ValueError("SITE_URL must be https://mkrting.com (or its www alias)")
BASE_URL = CANONICAL_ORIGIN
CONTACT_EMAIL = "mkrtingindia@gmail.com"
LINKEDIN_URL = "https://www.linkedin.com/company/mkrting/"
ACTIVE_NAV = {"Campaigns", "Guides", "About"}

# Publisher entity — used in JSON-LD and E-E-A-T signals across all pages
PUBLISHER = {
    "@type": "Organization",
    "name": "mkrting.com",
    "url": BASE_URL,
    "logo": {
        "@type": "ImageObject",
        "url": BASE_URL + "/assets/logo-512.png",
        "width": 512,
        "height": 512,
    },
    "email": CONTACT_EMAIL,
    "sameAs": [LINKEDIN_URL],
}


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Unsafe external URL: {value}")
    return value


def word_count(article: dict) -> int:
    """Approximate word count across all article section paragraphs."""
    words = 0
    for section in article.get("sections", []):
        for para in section.get("paragraphs", []):
            words += len(str(para).split())
        for bullet in section.get("bullets", []):
            words += len(str(bullet).split())
    words += len(str(article.get("dek", "")).split())
    words += len(str(article.get("signal", "")).split())
    words += len(str(article.get("lesson", "")).split())
    return max(words, 1)


def observability_scripts() -> str:
    """Add Vercel's project-specific static HTML scripts when configured."""
    scripts = []
    for env_name, namespace, queue in (
        ("VERCEL_WEB_ANALYTICS_SCRIPT_PATH", "va", "vaq"),
        ("VERCEL_SPEED_INSIGHTS_SCRIPT_PATH", "si", "siq"),
    ):
        path = os.getenv(env_name, "").strip()
        if not path:
            continue
        if not re.fullmatch(r"/[A-Za-z0-9_/-]+/script\.js", path) or "//" in path or "/../" in path:
            raise ValueError(f"{env_name} must be a project-specific /<path>/script.js URL path")
        scripts.append(f'<script>window.{namespace}=window.{namespace}||function(){{(window.{queue}=window.{queue}||[]).push(arguments)}};</script><script defer src="{e(path)}"></script>')
    return "\n  ".join(scripts)


def load_articles() -> list[dict]:
    result: list[dict] = []
    slugs: set[str] = set()
    for path in sorted(CONTENT.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))
        slug = article["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugs:
            raise ValueError(f"Invalid or duplicate slug in {path}")
        slugs.add(slug)
        for key in ("title", "seo_title", "seo_description", "reader_question", "dek", "kind", "category", "brand", "published", "updated", "sections", "sources", "lesson", "disclosure"):
            if not article.get(key):
                raise ValueError(f"Missing {key} in {path}")
        if len(article["sources"]) < 2:
            raise ValueError(f"Article needs at least two source links: {path}")
        for source in article["sources"]:
            safe_url(source["url"])
        if article.get("seo_title") and len(article["seo_title"]) > 120:
            raise ValueError(f"SEO title is too long in {path}")
        if article.get("seo_description") and len(article["seo_description"]) > 300:
            raise ValueError(f"SEO description is too long in {path}")
        if article.get("video_url"):
            safe_url(article["video_url"])
        datetime.fromisoformat(article["published"])
        datetime.fromisoformat(article["updated"])
        result.append(article)
    result.sort(key=lambda item: item["published"], reverse=True)
    return result


def load_guides() -> list[dict]:
    result = []
    for path in sorted(GUIDES.glob("*.json")):
        guide = json.loads(path.read_text(encoding="utf-8"))
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", guide.get("slug", "")):
            raise ValueError(f"Invalid guide slug: {path}")
        if not all(guide.get(key) for key in ("title", "dek", "published", "updated", "sections")):
            raise ValueError(f"Missing guide content: {path}")
        datetime.fromisoformat(guide["published"])
        datetime.fromisoformat(guide["updated"])
        result.append(guide)
    return result


def href(article: dict) -> str:
    return f"/campaigns/{article['slug']}/"


def breadcrumb_schema(parts: list[tuple[str, str]]) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": index + 1, "name": name, "item": BASE_URL + path} for index, (name, path) in enumerate(parts)]}


def article_schema(title: str, description: str, path: str, published: str, updated: str, breadcrumb: list[tuple[str, str]], image: str | None = None, word_count_val: int = 0, related_links: list[str] | None = None) -> dict:
    article_node: dict = {
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": published,
        "dateModified": updated,
        "author": {"@type": "Organization", "name": "mkrting.com", "url": BASE_URL + "/about/"},
        "publisher": PUBLISHER,
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE_URL + path},
        "isPartOf": {"@type": "WebSite", "@id": BASE_URL + "/", "name": "mkrting.com"},
        "inLanguage": "en-IN",
    }
    if image:
        article_node["image"] = {"@type": "ImageObject", "url": BASE_URL + image, "width": 1200, "height": 675}
    if word_count_val:
        article_node["wordCount"] = word_count_val
        minutes = max(1, round(word_count_val / 200))
        article_node["timeRequired"] = f"PT{minutes}M"
    if related_links:
        article_node["relatedLink"] = [BASE_URL + lnk for lnk in related_links]
    return {"@context": "https://schema.org", "@graph": [article_node, breadcrumb_schema(breadcrumb)]}


def guide_schema(guide: dict, path: str, articles: list[dict]) -> dict:
    """Generate FAQPage + HowTo + Article schema for guide pages."""
    faq_items = []
    for section in guide.get("sections", []):
        answer_text = " ".join(section.get("paragraphs", []))[:300]
        for question in section.get("questions", []):
            faq_items.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer_text},
            })
    how_to_steps = []
    for i, section in enumerate(guide.get("sections", []), 1):
        step_text = " ".join(section.get("paragraphs", []))[:200]
        how_to_steps.append({
            "@type": "HowToStep",
            "position": i,
            "name": section.get("heading", f"Step {i}"),
            "text": step_text,
        })
    article_node: dict = {
        "@type": "Article",
        "headline": guide["title"],
        "description": guide["dek"],
        "datePublished": guide["published"],
        "dateModified": guide["updated"],
        "author": {"@type": "Organization", "name": "mkrting.com", "url": BASE_URL + "/about/"},
        "publisher": PUBLISHER,
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE_URL + path},
        "isPartOf": {"@type": "WebSite", "@id": BASE_URL + "/", "name": "mkrting.com"},
        "inLanguage": "en-IN",
    }
    nodes: list[dict] = [article_node, breadcrumb_schema([("Home", "/"), ("Guides", "/guides/"), (guide["title"], path)])]
    if faq_items:
        nodes.append({"@type": "FAQPage", "mainEntity": faq_items})
    if how_to_steps:
        nodes.append({"@type": "HowTo", "name": guide["title"], "description": guide["dek"], "step": how_to_steps})
    return {"@context": "https://schema.org", "@graph": nodes}


def document(title: str, description: str, path: str, body: str, *, schema: dict | None = None, nav: str = "", meta_title: str | None = None, image: str | None = None, published: str | None = None, updated: str | None = None, article_category: str = "", article_kind: str = "", is_article: bool = False, is_guide: bool = False) -> str:
    url = BASE_URL + path
    page_title = meta_title or title
    page_title = page_title if "mkrting.com" in page_title.lower() else page_title + " | mkrting.com"
    schema_json = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c") if schema else ""
    schema_html = f'<script type="application/ld+json">{schema_json}</script>' if schema else ""
    image_meta = f'<meta property="og:image" content="{e(BASE_URL + image)}"><meta name="twitter:image" content="{e(BASE_URL + image)}">' if image else ""
    date_meta = f'<meta property="article:published_time" content="{e(published)}"><meta property="article:modified_time" content="{e(updated)}">' if published and updated else ""
    category_meta = f'<meta property="article:section" content="{e(article_category)}"><meta property="article:tag" content="{e(article_kind)}">' if article_category else ""
    og_type = "article" if (is_article or is_guide) else "website"
    author_meta = '<meta name="author" content="mkrting.com editorial">'
    author_link = f'<link rel="author" href="{e(BASE_URL + "/about/")}"> ' if (is_article or is_guide) else ""
    hreflang = f'<link rel="alternate" hreflang="en-IN" href="{e(url)}">'
    observability = observability_scripts()
    links = [("Campaigns", "/campaigns/"), ("India", "/india/"), ("Teardowns", "/teardowns/"), ("Guides", "/guides/"), ("About", "/about/")]
    menu = "".join('<a href="{}"{}>{}</a>'.format(link, ' aria-current="page"' if nav == label else '', label) for label, link in links if label in ACTIVE_NAV)
    return f'''<!doctype html>
<html lang="en-IN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{e(page_title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="theme-color" content="#e9e8df">
  {author_meta}
  {author_link}<link rel="canonical" href="{e(url)}">
  {hreflang}
  <link rel="icon" href="/assets/mkrting-favicon.png" type="image/png">
  <link rel="apple-touch-icon" href="/assets/mkrting-favicon.png">
  <link rel="alternate" href="/rss.xml" type="application/rss+xml" title="mkrting.com articles">
  <meta property="og:type" content="{og_type}"><meta property="og:site_name" content="mkrting.com">
  <meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{e(url)}">
  <meta name="twitter:card" content="{'summary_large_image' if image else 'summary'}">
  {image_meta}{date_meta}{category_meta}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap">
  <link rel="stylesheet" href="/assets/style.css">
  {schema_html}
  {observability}
</head>
<body>
  <div class="read-progress" id="read-progress" aria-hidden="true"></div>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="site-shell">
    <header class="topbar">
      <a class="wordmark" href="/" aria-label="mkrting.com home">mkrting<span class="wordmark-dot">.</span>com</a>
      <nav class="nav" aria-label="Main navigation">{menu}</nav>
      <a class="topbar-index" href="/method/">Our method <span aria-hidden="true">↗</span></a>
    </header>
    <main id="main">{body}</main>
    <footer class="footer">
      <div class="footer-intro">
        <a class="footer-mark" href="/" aria-label="mkrting.com home">mkrting<span>.</span>com</a>
        <p>Independent analysis of the decisions behind marketing campaigns.</p>
        <a class="footer-email" href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      </div>
      <nav class="footer-nav" aria-label="Footer navigation">
        <div><span>Explore</span><a href="/campaigns/">Campaigns</a><a href="/india/">India</a><a href="/guides/">Guides</a><a href="/rss.xml">RSS feed</a></div>
        <div><span>Publication</span><a href="/about/">About</a><a href="/method/">Method</a><a href="/corrections/">Corrections</a><a href="/contact/">Contact</a></div>
        <div><span>Legal &amp; social</span><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">LinkedIn <b aria-hidden="true">&#8599;</b></a></div>
      </nav>
      <div class="footer-bottom"><span>&copy; {datetime.now(timezone.utc).year} mkrting.com. Privately owned.</span><span>India-first / world-aware</span></div>
    </footer>
  </div>
</body>
</html>'''


def article_card(article: dict, index: int) -> str:
    return f'''<a class="story-card" href="{href(article)}">
      <div class="story-card-top"><span>{e(article['kind'])}</span><span>{index:02d}</span></div>
      <div class="card-art card-art-{index % 3}" aria-hidden="true"><span>{e(article['brand'][:1].upper())}</span><i></i></div>
      <div class="story-meta"><span>{e(article['category'])}</span><span>{e(article['published'])}</span></div>
      <h3>{e(article['title'])}</h3><p>{e(article['dek'])}</p>
      <span class="card-read">Read the analysis <span aria-hidden="true">↗</span></span>
    </a>'''


def home_page(articles: list[dict]) -> str:
    latest = articles[0] if articles else None
    featured = ""
    if latest:
        featured = f'''<section class="feature" aria-labelledby="feature-title">
          <div class="section-label"><span>01 / Featured analysis</span><span>Fresh thinking, sourced</span></div>
          <a class="feature-link" href="{href(latest)}"><div class="feature-visual" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><span class="feature-initial">{e(latest['brand'][:1].upper())}</span><span class="feature-stamp">MKR / 001</span></div>
            <div class="feature-copy"><span class="eyebrow">{e(latest['category'])} / {e(latest['kind'])}</span><h2 id="feature-title">{e(latest['title'])}</h2><p>{e(latest['dek'])}</p><div class="feature-lesson"><span>THE TAKEAWAY</span><strong>{e(latest['lesson'])}</strong></div><span class="round-arrow" aria-label="Read analysis">&#8599;</span></div></a>
        </section>'''
    recent = "".join(article_card(article, index + 1) for index, article in enumerate(articles[:6]))
    body = f'''<section class="hero"><div class="hero-kicker"><span class="pulse"></span> An independent marketing intelligence journal <span class="hero-issue">India-first / world-aware</span></div>
      <h1>Marketing<br><em>Decoded<span class="hero-period">.</span></em></h1>
      <div class="hero-bottom"><p>Campaigns move fast. We slow down to find the idea underneath&#8212;the audience, the creative choice, and the lesson worth keeping.</p><a class="hero-cta" href="/campaigns/">Explore the campaigns <span>&#8599;</span></a></div>
    </section>
    <div class="ticker" aria-label="Editorial focus"><div>CAMPAIGNS <b>&#10003;</b> BRAND STRATEGY <b>&#10003;</b> DESIGN <b>&#10003;</b> STARTUP LESSONS <b>&#10003;</b> CAMPAIGNS <b>&#10003;</b> BRAND STRATEGY <b>&#10003;</b> DESIGN <b>&#10003;</b></div></div>
    {featured}
    <section class="latest" aria-labelledby="latest-title"><div class="section-label"><span>02 / The reading list</span><a href="/campaigns/">View all campaigns &#8599;</a></div><div class="latest-heading"><h2 id="latest-title">Worth a<br><em>closer look.</em></h2><p>Recent campaigns and the strategic decisions behind them.</p></div><div class="story-grid">{recent}</div></section>
    <section class="guide-promo"><span>FREE RESEARCH GUIDE / 07 STEPS</span><h2>Look at a campaign.<br><em>See the decisions.</em></h2><p>Use our evidence-first worksheet to analyse the brief, audience, creative and results behind any marketing campaign.</p><a href="/guides/campaign-analysis/">Explore the campaign analysis guide &#8599;</a></section>
    <section class="manifesto"><div class="manifesto-number">03 / OUR POINT OF VIEW</div><p>Good marketing is more than a <em>good-looking ad.</em> We look for the decision that made it matter.</p><a href="/method/">How we evaluate campaigns <span>&#8599;</span></a></section>
    <section class="questions"><div class="section-label"><span>04 / The questions we ask</span><span>Every story earns its place</span></div><div class="questions-grid"><div><span>01</span><h3>What changed?</h3><p>The market moment, audience tension or product truth that shaped the brief.</p></div><div><span>02</span><h3>Why this idea?</h3><p>The choice in the creative and how people were meant to encounter it.</p></div><div><span>03</span><h3>What can travel?</h3><p>A principle a smaller team could apply without copying the campaign.</p></div></div></section>'''
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": BASE_URL + "/",
                "name": "mkrting.com",
                "url": BASE_URL + "/",
                "description": "Independent analysis of marketing campaigns, brand strategy, design and startup lessons, with an India-first perspective.",
                "inLanguage": "en-IN",
            },
            {
                "@type": "Organization",
                "@id": BASE_URL + "/#organization",
                "name": "mkrting.com",
                "url": BASE_URL,
                "logo": {"@type": "ImageObject", "url": BASE_URL + "/assets/logo-512.png", "width": 512, "height": 512},
                "description": "India-first marketing and brand strategy journal covering campaign analysis, creative decisions and startup lessons.",
                "email": CONTACT_EMAIL,
                "sameAs": [LINKEDIN_URL],
                "foundingDate": "2026",
                "knowsAbout": ["marketing strategy", "brand strategy", "campaign analysis", "Indian marketing", "startup marketing"],
            },
        ],
    }
    return document("Marketing campaigns and brand strategy, decoded", "Independent analysis of marketing campaigns, brand strategy, design and startup lessons, with an India-first perspective.", "/", body, schema=schema)


def article_page(article: dict, related: list[dict]) -> str:
    section_html = []
    for section in article["sections"]:
        paragraphs = "".join(f"<p>{e(text)}</p>" for text in section.get("paragraphs", []))
        bullets = "<ul>" + "".join(f"<li>{e(text)}</li>" for text in section["bullets"]) + "</ul>" if section.get("bullets") else ""
        section_html.append(f'<section class="article-section"><h2>{e(section["heading"])}</h2>{paragraphs}{bullets}</section>')
        if article.get("analysis_image") and section["heading"] == article.get("analysis_after"):
            analysis_image = article["analysis_image"]
            if not analysis_image.startswith("/assets/") or not (ASSETS / analysis_image.removeprefix("/assets/")).is_file() or not article.get("analysis_alt"):
                raise ValueError(f"Article analysis image and alt text are invalid: {article['slug']}")
            section_html.append(f'<figure class="article-figure article-explainer"><img src="{e(analysis_image)}" width="1200" height="675" alt="{e(article["analysis_alt"])}" loading="lazy"><figcaption>{e(article.get("analysis_caption", "Original mkrting.com analysis graphic."))}</figcaption></figure>')
    sources = "".join(f'<li><span>{e(source["type"])}</span><a href="{e(source["url"])}" target="_blank" rel="noopener noreferrer">{e(source["label"])} &#8599;</a></li>' for source in article["sources"])
    creative = f'<a class="creative-link" href="{e(article["video_url"])}" target="_blank" rel="noopener noreferrer"><span>&#9654;</span><strong>Watch the original campaign</strong><small>Opens at the source &#8599;</small></a>' if article.get("video_url") else ""
    image_path = article.get("hero_image")
    if image_path:
        if not image_path.startswith("/assets/") or not (ASSETS / image_path.removeprefix("/assets/")).is_file() or not article.get("hero_alt"):
            raise ValueError(f"Article image and alt text are invalid: {article['slug']}")
        hero_width = int(article.get("hero_width", 1200))
        hero_height = int(article.get("hero_height", 675))
        if hero_width < 1 or hero_height < 1:
            raise ValueError(f"Article image dimensions are invalid: {article['slug']}")
        art = f'<figure class="article-figure"><img src="{e(image_path)}" width="{hero_width}" height="{hero_height}" alt="{e(article["hero_alt"])}" fetchpriority="high"><figcaption>{e(article.get("hero_caption", "Original mkrting.com analysis graphic."))}</figcaption></figure>'
    else:
        art = f'<div class="article-art" aria-hidden="true"><span>{e(article["brand"][:1].upper())}</span><i>CAMPAIGN / DECODED</i></div>'
    related_cards = "".join(f'<li><a href="{href(item)}">{e(item["title"])} <span>&#8599;</span></a></li>' for item in related[:3])
    related_links_for_schema = [href(item) for item in related[:3]]
    related_html = f'<section class="article-related"><h2>Keep reading</h2><ul><li><a href="/guides/campaign-analysis/">How to analyse a marketing campaign <span>&#8599;</span></a></li>{related_cards}</ul></section>'
    body = f'''<article class="article"><div class="article-head"><div class="breadcrumb"><a href="/">Home</a> / <a href="/campaigns/">Campaigns</a> / {e(article['brand'])}</div><div class="article-tags"><span>{e(article['category'])}</span><span>{e(article['kind'])}</span></div><h1>{e(article['title'])}</h1><p class="article-dek">{e(article['dek'])}</p><div class="article-byline"><div>mkrting.com <span>Editorial desk</span></div><div>Published <time datetime="{e(article['published'])}">{e(article['published'])}</time><br>Updated <time datetime="{e(article['updated'])}">{e(article['updated'])}</time></div><div>{e(article['read_minutes'])} min read</div></div></div>
      <div class="article-layout"><aside class="article-rail"><div class="rail-label">The core idea</div><p>{e(article['signal'])}</p><div class="rail-rule"></div><div class="rail-label">The lesson</div><p>{e(article['lesson'])}</p><a href="#sources">View sources &#8595;</a></aside><div class="article-body">{art}{creative}{''.join(section_html)}<div class="article-takeaway"><span>THE STARTUP TAKEAWAY</span><p>{e(article['lesson'])}</p></div><section class="article-sources" id="sources"><h2>Sources &amp; notes</h2><p>Source links document the campaign and reporting. Strategic interpretation is mkrting.com&#39;s own.</p><ul>{sources}</ul><p class="disclosure">{e(article['disclosure'])}</p><p class="disclosure">Found an error? Read our <a href="/corrections/">corrections policy</a>.</p></section>{related_html}</div></div></article>'''
    wc = word_count(article)
    schema = article_schema(
        article["title"], article["dek"], href(article),
        article["published"], article["updated"],
        [("Home", "/"), ("Campaigns", "/campaigns/"), (article["brand"], href(article))],
        image_path, word_count_val=wc, related_links=related_links_for_schema,
    )
    return document(
        article["title"], article.get("seo_description", article["dek"]), href(article), body,
        schema=schema, meta_title=article.get("seo_title"), image=image_path,
        published=article["published"], updated=article["updated"],
        article_category=article.get("category", ""), article_kind=article.get("kind", ""),
        is_article=True,
    )


def listing_page(title: str, subtitle: str, articles: list[dict], path: str, nav: str = "") -> str:
    cards = "".join(article_card(article, index + 1) for index, article in enumerate(articles))
    body = f'''<section class="listing-head"><div class="section-label"><span>MKR / INDEX</span><span>{len(articles):02d} stories</span></div><h1>{e(title)}<span>.</span></h1><p>{e(subtitle)}</p></section><section class="listing-grid story-grid">{cards}</section>'''
    return document(title, subtitle, path, body, nav=nav)


def guides_page(guides: list[dict]) -> str:
    cards = "".join(f'<a class="guide-index-card" href="/guides/{e(guide["slug"])}/"><span>RESEARCH GUIDE / {index:02d}</span><h2>{e(guide["title"])}</h2><p>{e(guide["dek"])}</p><strong>Read the guide &#8599;</strong></a>' for index, guide in enumerate(guides, 1))
    body = f'<section class="listing-head"><div class="section-label"><span>MKR / FIELD NOTES</span><span>{len(guides):02d} guides</span></div><h1>Guides<span>.</span></h1><p>Practical ways to understand campaigns and make better marketing decisions.</p></section><div class="guide-index">{cards}</div>'
    return document("Marketing strategy guides and templates", "Practical research guides for analysing marketing campaigns, brand strategy and startup marketing.", "/guides/", body, nav="Guides")


def guide_page(guide: dict, articles: list[dict]) -> str:
    path = f'/guides/{guide["slug"]}/'
    content = []
    for section in guide["sections"]:
        paragraphs = "".join(f'<p>{e(paragraph)}</p>' for paragraph in section["paragraphs"])
        questions = "".join(f'<li>{e(question)}</li>' for question in section.get("questions", []))
        content.append(f'<section class="guide-section"><h2>{e(section["heading"])}</h2>{paragraphs}<div class="guide-questions"><strong>Ask yourself</strong><ul>{questions}</ul></div></section>')
    example = next((article for article in articles if article["slug"] == guide.get("example_article")), None)
    example_link = f'<aside class="guide-example"><span>SEE THE METHOD IN USE</span><p>Our <a href="{href(example)}">{e(example["brand"])} campaign analysis</a> traces the product role and states which outcomes remain unknown.</p></aside>' if example else ""
    guide_num = guide.get("guide_number", "01")
    body = f'''<article class="guide"><div class="guide-header"><div class="breadcrumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {e(guide["title"])}</div><span class="guide-kicker">THE MKR FIELD GUIDE / {guide_num}</span><h1>{e(guide['title'])}<span>.</span></h1><p>{e(guide['dek'])}</p><div class="guide-dates">Published <time datetime="{e(guide['published'])}">{e(guide['published'])}</time> &#183; Updated <time datetime="{e(guide['updated'])}">{e(guide['updated'])}</time></div></div><div class="guide-layout"><aside class="guide-summary"><strong>THE WORKSHEET</strong><ol><li>Original work</li><li>Business problem</li><li>Audience tension</li><li>Brand role</li><li>Creative mechanism</li><li>Outcome evidence</li><li>Transferable lesson</li></ol><p>Keep observations, source claims and your own interpretation separate.</p></aside><div class="guide-content">{''.join(content)}{example_link}<section class="guide-download"><h2>Use this on your next campaign</h2><p>Copy the seven questions into a working document. Record a URL beside every factual answer and write &#8220;unknown&#8221; where the evidence stops. Return to the campaign after it has run if credible outcome data becomes available.</p><a href="/campaigns/">Browse campaign analyses &#8599;</a></section></div></div></article>'''
    schema = guide_schema(guide, path, articles)
    return document(guide["title"], guide["dek"], path, body, schema=schema, meta_title=guide.get("seo_title"), published=guide["published"], updated=guide["updated"], is_guide=True)


def text_page(title: str, kicker: str, lead: str, sections: list[tuple[str, str]], path: str, nav: str = "") -> str:
    email_link = f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>'
    block = "".join(f'<section><h2>{e(heading)}</h2><p>{e(copy).replace(CONTACT_EMAIL, email_link)}</p></section>' for heading, copy in sections)
    body = f'''<div class="text-page"><div class="section-label"><span>{e(kicker)}</span><span>mkrting.com</span></div><h1>{e(title)}<span>.</span></h1><p class="text-lead">{e(lead)}</p><div class="text-sections">{block}</div></div>'''
    return document(title, lead, path, body, nav=nav)


def contact_page() -> str:
    body = f'''<div class="text-page"><div class="section-label"><span>04 / CONTACT</span><span>mkrting.com</span></div><h1>Contact<span>.</span></h1><p class="text-lead">Questions, corrections, permissions and privacy requests reach the publication directly.</p><div class="text-sections">
      <section><h2>Email us</h2><p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p><p>For a factual correction, include the article URL, the sentence at issue and a reliable source. For permissions, identify the content you want to reuse and where it will appear.</p></section>
      <section><h2>Find us on LinkedIn</h2><p><a href="{LINKEDIN_URL}" target="_blank" rel="noopener noreferrer">mkrting.com on LinkedIn &#8599;</a></p><p>LinkedIn is an external service with its own privacy terms.</p></section>
      <section><h2>Editorial independence</h2><p>Contacting us does not guarantee coverage or a particular editorial outcome. We distinguish factual corrections from requests to change an independent analysis.</p></section>
    </div></div>'''
    return document("Contact", "Contact mkrting.com for corrections, permissions, privacy requests and editorial questions.", "/contact/", body)


def write(path: str, content: str) -> None:
    target = DIST / path.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build() -> None:
    articles = load_articles()
    guides = load_guides()
    india = [item for item in articles if item["category"] == "India"]
    teardowns = [item for item in articles if item["kind"].lower() == "campaign teardown"]
    ACTIVE_NAV.clear()
    ACTIVE_NAV.update({"Campaigns", "Guides", "About"})
    if len(india) >= 3:
        ACTIVE_NAV.add("India")
    if len(teardowns) >= 3:
        ACTIVE_NAV.add("Teardowns")
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ASSETS, DIST / "assets")
    write("index.html", home_page(articles))
    for article in articles:
        related = sorted((item for item in articles if item["slug"] != article["slug"]), key=lambda item: (item["category"] == article["category"], item["brand"] == article["brand"], item["published"]), reverse=True)
        write(href(article) + "index.html", article_page(article, related))
    write("guides/index.html", guides_page(guides))
    for guide in guides:
        write(f"guides/{guide['slug']}/index.html", guide_page(guide, articles))
    write("campaigns/index.html", listing_page("Campaigns", "Browse original analysis of marketing campaigns, creative decisions and the brand strategy behind the work.", articles, "/campaigns/", "Campaigns"))
    if "India" in ACTIVE_NAV:
        write("india/index.html", listing_page("India", "Explore Indian marketing campaigns and the audience insights, creative choices and brand decisions behind them.", india, "/india/", "India"))
    if "Teardowns" in ACTIVE_NAV:
        write("teardowns/index.html", listing_page("Teardowns", "Evidence-led campaign teardowns that explain the audience, creative mechanism and practical lesson.", teardowns, "/teardowns/", "Teardowns"))
    write("about/index.html", text_page("About us", "01 / ABOUT", "We study what brands make, and why people might care. Our starting point is India; our curiosity is global.", [
        ("Our purpose", "mkrting.com is an independent publication for founders, marketers and designers who want to understand the strategy behind a campaign. Founded in 2026, we bring an evidence-first approach to Indian brand marketing: we verify the original creative, identify the audience insight, and explain the strategic choice in terms a smaller team can use."),
        ("What we publish", "Original campaign teardowns, evidence-led brand strategy analyses and practical startup marketing playbooks. Coverage is not guaranteed to a brand or agency. We publish when a campaign offers a genuine idea and enough verified evidence to discuss it honestly and accurately."),
        ("Our editorial standards", "Every article cites primary sources. Strategic readings are labelled as interpretation. Performance claims require verifiable measurement data, not publicity figures. AI assists research and drafting; a human editor reviews and approves every article before publication."),
        ("How we use AI", "Automation helps us find leads, group duplicate stories, organise evidence and prepare drafts. The editorial decision — what to publish and what to hold — is made by a person. Source links, evidence limits and corrections remain visible on every article."),
        ("Corrections", "We review challenged facts against linked evidence and update confirmed errors. Material corrections are noted on the article, and its modification date is updated. Our corrections policy is available at /corrections/."),
        ("Ownership and contact", "mkrting.com is privately owned. Reach the publication at mkrtingindia@gmail.com or through our official LinkedIn company page. The Contact, Privacy and Terms pages explain how readers can reach us and use this site."),
    ], "/about/", "About"))
    write("method/index.html", text_page("Our method", "02 / METHODOLOGY", "Every article starts with a question: what can a reader learn here that the announcement itself cannot explain?", [
        ("Find the original", "We look for the brand's campaign page, official creative, agency release or first-party material. Trade publications and social curators help discover stories and corroborate details. A curator's post is a lead, not a fact."),
        ("Separate fact from interpretation", "Dates, credits, product claims and performance figures need sources. Our analysis of the strategic idea is clearly labelled as interpretation. A view count is not proof of business impact. We record what the evidence establishes and what it cannot prove."),
        ("The evidence gate", "A story is held until it has a verified primary source — the brand's own campaign material — and at least one independent report from a separate domain. This gate prevents analysis built entirely on press releases or social posts without corroboration."),
        ("Respect the work", "We link to original reporting and creative. Credit does not grant permission to republish an article or image; we use licensed material, permitted embeds or original mkrting.com artwork."),
        ("Correct openly", "When a material error is reported, we check the underlying evidence, update the article and mark its modification date. The corrections route is listed on every article."),
    ], "/method/"))
    write("corrections/index.html", text_page("Corrections", "03 / ACCOUNTABILITY", "How mkrting.com checks challenged claims, corrects factual errors and records material changes to published analysis.", [
        ("How corrections work", "We review challenged facts against the linked evidence and update confirmed errors. Material corrections are noted on the article, with the updated date. We do not silently delete or redate published content."),
        ("Report an error", "Email mkrtingindia@gmail.com with the article URL, the exact claim and a source that supports the correction. We review factual issues and update confirmed errors; a request to change an opinion or strategic interpretation is considered separately."),
    ], "/corrections/"))
    write("contact/index.html", contact_page())
    write("privacy/index.html", text_page("Privacy policy", "05 / PRIVACY", "How this independent publication handles information when you read the site or contact us. Last updated 23 September 2026.", [
        ("Who operates the site", "mkrting.com is a privately owned publication. Privacy requests can be sent to mkrtingindia@gmail.com."),
        ("Information we receive", "When you browse the site, our hosting provider may process technical request data such as your IP address, browser information, pages requested and request time to deliver and protect the site. When you email us, we receive your address and the information you choose to send. This site currently has no reader account, comment form or newsletter signup."),
        ("Analytics and external services", "If enabled, Vercel Web Analytics provides aggregate page and referral statistics without third-party tracking cookies; Vercel Speed Insights may collect performance measurements. The site loads a font stylesheet from Google Fonts, so your browser may contact Google. Links to LinkedIn and cited sources take you to services governed by their own policies."),
        ("Why we use information", "We use technical data to operate, secure and understand the site. We use messages to answer requests, investigate corrections, handle permissions and keep necessary records. Reader emails are not fed into the article drafting system."),
        ("Sharing and storage", "Vercel hosts the website; Google provides the font service; Google Gmail handles our mailbox. These providers may process data outside India under their own terms. We do not sell reader information. We retain correspondence only as needed for the purpose of the exchange, legitimate records or legal obligations; provider logs follow provider retention settings."),
        ("Your choices", "You can ask about, correct or request deletion of information you sent us by emailing mkrtingindia@gmail.com. We will review the request under applicable law and any record-keeping obligations. You can avoid sending personal information in a message unless it is needed for your request."),
        ("Changes", "We will update this page when the site adds material data collection, a newsletter, advertising technology or other new services. The date above will change when the policy changes."),
    ], "/privacy/"))
    write("terms/index.html", text_page("Terms of use", "06 / TERMS", "Terms for reading, linking to and reusing material from mkrting.com. Last updated 23 September 2026.", [
        ("The publication", "mkrting.com is an independently and privately owned editorial publication. Its articles analyse marketing, branding and startup strategy for general information. They are not business, legal, financial or other professional advice."),
        ("Accuracy and corrections", "We aim to distinguish sourced facts from strategic interpretation, but campaigns, prices, offers and third-party pages can change. Check original sources before relying on time-sensitive details. Send a factual correction to mkrtingindia@gmail.com with the article URL and supporting evidence."),
        ("Original work and reuse", "Unless stated otherwise, original mkrting.com writing, layout and illustrations belong to the site owner. You may link to pages and quote brief excerpts with clear credit and a link. For full republication, translation, commercial reuse or use of our graphics, request permission at mkrtingindia@gmail.com."),
        ("Brands and third-party material", "Brand names, logos and campaign materials remain the property of their respective owners. Discussion of a campaign does not imply endorsement, sponsorship or affiliation. External sites and social platforms have their own terms and privacy practices."),
        ("Reader conduct", "Do not attempt to disrupt the website, impersonate the publication or use its material in a way that misrepresents our analysis. Automated access must respect the site's technical controls and applicable law."),
        ("Availability and responsibility", "The site may change, pause or remove content. We cannot guarantee uninterrupted access or that every external link remains available. Any limitation of responsibility applies only to the extent permitted by applicable law."),
        ("Contact and changes", "Questions about these terms or permissions can be sent to mkrtingindia@gmail.com. We may update these terms as the publication develops and will show a revised date on this page. Applicable Indian law governs these terms, subject to mandatory rights that law preserves."),
    ], "/terms/"))
    latest_article = max((article["updated"] for article in articles), default="")
    latest_guide = max((guide["updated"] for guide in guides), default="")
    latest_any = max(latest_article, latest_guide)
    urls: list[tuple[str, str]] = [("/", latest_any), ("/campaigns/", latest_article), ("/guides/", latest_guide), ("/about/", ""), ("/method/", ""), ("/corrections/", ""), ("/contact/", ""), ("/privacy/", ""), ("/terms/", "")]
    if "India" in ACTIVE_NAV:
        urls.append(("/india/", max(item["updated"] for item in india)))
    if "Teardowns" in ACTIVE_NAV:
        urls.append(("/teardowns/", max(item["updated"] for item in teardowns)))
    urls.extend((href(article), article["updated"]) for article in articles)
    urls.extend((f"/guides/{guide['slug']}/", guide["updated"]) for guide in guides)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f'<url><loc>{xml_escape(BASE_URL + path)}</loc>{f"<lastmod>{xml_escape(lastmod)}</lastmod>" if lastmod else ""}</url>' for path, lastmod in urls) + "</urlset>"
    write("sitemap.xml", sitemap)
    items = "".join(f'<item><title>{xml_escape(article["title"])}</title><link>{xml_escape(BASE_URL + href(article))}</link><guid>{xml_escape(BASE_URL + href(article))}</guid><description>{xml_escape(article["dek"])}</description><pubDate>{datetime.fromisoformat(article["published"]).replace(tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate></item>' for article in articles)
    write("rss.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>mkrting.com</title><link>{xml_escape(BASE_URL)}</link><description>The strategy behind the campaign.</description>{items}</channel></rss>')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print(f"Built {len(articles)} articles, {len(guides)} guides and {len(urls)} indexable URLs in {DIST}")


if __name__ == "__main__":
    build()

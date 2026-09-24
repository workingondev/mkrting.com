"""Build the reviewed source watchlist from the editorial source map."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDS = json.loads((ROOT / "data/feeds.json").read_text())

# These are discovery candidates, not verified crawl endpoints. An editor must
# verify access and an actual collector before moving one into feeds.json.
WATCHLIST = """
Exchange4media|India|independent_reporting,distribution|marketing,media|search_monitor
Storyboard18|India|independent_reporting,strategy|brands,consumer|search_monitor
BestMediaInfo|India|discovery,independent_reporting|advertising,media|sitemap_diff
Agency Reporter|India|independent_reporting,adtech,distribution|programmatic,ctv|sitemap_diff
IMPACT|India|independent_reporting,strategy|interviews,creative|search_monitor
Pitch|India|consumer_data,strategy|ad_spend,media_economics|search_monitor
MediaBrief|India|discovery|campaigns,announcements|sitemap_diff
Adgully|India|discovery|advertising,entertainment|search_monitor
Passionate in Marketing|India|discovery|campaigns,marketing|rss_candidate
BuzzInContent|India|independent_reporting,creator_social|branded_content|search_monitor
Social Ketchup|India|creator_social,discovery|influencers,social|search_monitor
Creative Gaga|India|branding,creative_archive|identity,design|search_monitor
IndiaRetailing|India|startup,consumer_data|retail,d2c|search_monitor
IndianTelevision.com|India|independent_reporting,distribution|broadcast,media|rss_candidate
The Drum|Global|independent_reporting,strategy|creative,agencies|search_monitor
Campaign|Global|independent_reporting,strategy|creative,agencies|manual_or_paid
Marketing Week|Global|strategy,effectiveness|marketing_strategy|search_monitor
Digiday|Global|independent_reporting,distribution|digital_media|search_monitor
Little Black Book|Global|creative_archive,independent_reporting|campaign_credits,production|database_monitor
Ads of the World|Global|creative_archive|campaign_credits,creative|database_monitor
WARC|Global|effectiveness,research_archive|case_studies,marketing_data|manual_or_paid
Contagious|Global|strategy,research_archive|creative_strategy|manual_or_paid
Brand New|Global|branding,creative_archive|rebrands,identity|manual_or_paid
Transform Magazine|Global|branding,strategy|rebrands,identity|rss_candidate
Brandingmag|Global|branding,strategy|brand_strategy|rss_candidate
BP&O|Global|branding,creative_archive|identity,packaging|rss_candidate
DIELINE|Global|branding,creative_archive|packaging,identity|rss_candidate
Creative Boom|Global|branding,creative_archive|design,identity|rss_candidate
It's Nice That|Global|branding,creative_archive|design,inspiration|rss_candidate
Fast Company Design|Global|branding,strategy|design,innovation|rss_candidate
Creative Bloq|Global|branding,creative_archive|design,trends|rss_candidate
Packaging of the World|Global|creative_archive,branding|packaging|rss_candidate
The Brand Identity|Global|branding,creative_archive|identity,design|search_monitor
Search Engine Land|Global|distribution,strategy|search,seo|rss_candidate
MarTech|Global|adtech,distribution|marketing_operations|rss_candidate
AdExchanger|Global|adtech,distribution|programmatic,retail_media|rss_candidate
Social Media Today|Global|creator_social,distribution|social_platforms|rss_candidate
Buffer|Global|creator_social,research_archive|social_data|search_monitor
Later|Global|creator_social|instagram,tiktok|search_monitor
Sprout Social Insights|Global|creator_social,consumer_data|social_research|search_monitor
Influencer Marketing Hub|Global|creator_social,research_archive|creator_economy|search_monitor
Tubefilter|Global|creator_social|youtube,creators|search_monitor
Kyoorius Creative Awards|India|award_database,creative_archive|advertising,design|database_monitor
Kyoorius Marketing Awards|India|award_database,effectiveness|strategy,effectiveness|database_monitor
ABBY / Goafest|India|award_database,creative_archive|advertising,media|database_monitor
Cannes Lions / The Work|Global|award_database,creative_archive|creative_awards|manual_or_paid
Effie Awards|Global|award_database,effectiveness|marketing_effectiveness|database_monitor
D&AD Awards|Global|award_database,creative_archive|design,advertising|database_monitor
Clio Awards|Global|award_database,creative_archive|advertising,design|database_monitor
The One Show|Global|award_database,creative_archive|advertising,design|database_monitor
Official brand newsroom|Global|primary_evidence|brand_claims,launches|manual_or_paid
Official agency case study|Global|primary_evidence|creative_credits,campaign_assets|manual_or_paid
Official brand YouTube|Global|primary_evidence|campaign_films|youtube_channel_rss
"""


def slug(name):
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    result = []
    for feed in FEEDS:
        name = feed["name"]
        if name.startswith("ET Brand Equity"):
            group = "et-brand-equity"
        else:
            group = feed["id"]
        roles = ["discovery", "independent_reporting"] if feed["source_type"] == "trade_media" else ["discovery"]
        if name in {"Marketing Mind", "Social Samosa", "MediaNews4U"}:
            roles = ["discovery"]
        if name in {"YourStory", "Inc42 Startups", "TechCrunch"}:
            roles = ["discovery", "startup"]
        if name == "Design Week":
            roles = ["branding", "creative_archive"]
        result.append({"id": feed["id"], "name": name, "source_group": group,
                       "region": feed["region"], "roles": roles,
                       "specialties": [], "collector": "rss", "url": feed["url"],
                       "status": "active" if feed["enabled"] else "needs_runtime_verification",
                       "content_ingestion": "metadata_only", "evidence_class": "lead_only"})
    for raw in WATCHLIST.strip().splitlines():
        name, region, roles, specialties, collector = raw.split("|")
        existing = next((source for source in result if source["id"] == slug(name) or source["name"] == name), None)
        if existing:
            existing["roles"] = roles.split(",")
            existing["specialties"] = specialties.split(",")
            continue
        result.append({"id": slug(name), "name": name, "source_group": slug(name),
                       "region": region, "roles": roles.split(","),
                       "specialties": specialties.split(","), "collector": collector,
                       "url": None, "status": "research_watchlist", "content_ingestion": "none",
                       "evidence_class": "manual_review_required"})
    ids = [source["id"] for source in result]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source id")
    (ROOT / "data/sources.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(result)} sources ({sum(s['status'] == 'active' for s in result)} active RSS)")


if __name__ == "__main__":
    main()

"""Check the evidence gate and dedupe behavior that protect publication quality."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import engine  # noqa: E402
import seo_report  # noqa: E402


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.old_local, self.old_db = engine.LOCAL, engine.DB
        engine.LOCAL = Path(self.temp.name)
        engine.DB = engine.LOCAL / "test.db"
        self.db = engine.init_db()

    def tearDown(self) -> None:
        self.db.close()
        engine.LOCAL, engine.DB = self.old_local, self.old_db
        self.temp.cleanup()

    def test_source_gate_and_url_dedupe(self) -> None:
        cluster, created = engine.add_item(self.db, url="https://news.example/amaron?utm_source=x", title="Amaron launches Modern Bikes campaign", summary="", source_name="Trade", source_type="trade_media", region="India")
        self.assertTrue(created)
        same, created = engine.add_item(self.db, url="https://news.example/amaron", title="Amaron launches Modern Bikes campaign", summary="", source_name="Trade", source_type="trade_media", region="India")
        self.assertEqual((same, created), (cluster, False))
        self.assertFalse(engine.shortlist(self.db)[0]["ready_for_draft"])
        engine.add_item(self.db, url="https://brand.example/modern-bikes", title="Official Modern Bikes creative", summary="", source_name="Brand", source_type="primary", region="India", is_primary=True, cluster_id=cluster)
        self.assertTrue(engine.shortlist(self.db)[0]["ready_for_draft"])

    def test_unrelated_stories_stay_separate(self) -> None:
        first, _ = engine.add_item(self.db, url="https://news.example/a", title="Amaron launches modern bikes campaign", summary="", source_name="Trade", source_type="trade_media", region="India")
        second, _ = engine.add_item(self.db, url="https://news.example/b", title="Zomato launches new packaging campaign", summary="", source_name="Trade", source_type="trade_media", region="India")
        self.assertNotEqual(first, second)

    def test_two_first_party_sources_do_not_replace_independent_reporting(self) -> None:
        cluster, _ = engine.add_item(self.db, url="https://brand.example/launch", title="Example launches identity campaign", summary="", source_name="Brand", source_type="primary", region="India", is_primary=True)
        engine.add_item(self.db, url="https://agency.example/work", title="Example identity campaign case study", summary="", source_name="Agency", source_type="primary", region="India", is_primary=True, cluster_id=cluster)
        self.assertFalse(engine.shortlist(self.db)[0]["ready_for_draft"])
        engine.add_item(self.db, url="https://news.example/example", title="Example identity campaign covered", summary="", source_name="Trade", source_type="trade_media", region="India", cluster_id=cluster)
        self.assertTrue(engine.shortlist(self.db)[0]["ready_for_draft"])

    def test_research_ledger_rejects_unsourced_claim(self) -> None:
        research = {"ready": True, "claims": [{"fact": f"Fact {i}", "source_url": "https://unknown.example/story" if i == 3 else "https://brand.example/story", "confidence": "high"} for i in range(1, 4)], "unknowns": [], "strategic_angle": "An original audience insight"}
        self.assertIn("claim 3 needs a supplied source and high/medium confidence", engine.validate_research(research, {"https://brand.example/story"}))

    def test_feed_health_reports_runtime_status_separately_from_registry(self) -> None:
        engine.record_feed_run(self.db, "marketing-mind", "failed", 0, 0, "network unavailable")
        health = {item["id"]: item for item in engine.feed_health(self.db)}
        self.assertTrue(health["marketing-mind"]["enabled"])
        self.assertEqual(health["marketing-mind"]["latest"]["status"], "failed")

    def test_local_category_classification(self) -> None:
        self.assertEqual(engine.classify("A startup reveals a new packaging identity"), "branding")
        self.assertEqual(engine.classify("Brand launches a campaign film"), "advertising")
        self.assertEqual(engine.classify("A D2C startup explains its marketing strategy"), "startup")

    def test_generated_article_must_cite_primary(self) -> None:
        article_paths = sorted((Path(__file__).resolve().parents[1] / "content/articles").glob("*.json"))
        self.assertTrue(article_paths)
        article = json.loads(article_paths[0].read_text())
        urls = {source["url"] for source in article["sources"]}
        self.assertEqual(engine.validate_draft(article, urls, {article["sources"][0]["url"]}), [])
        self.assertIn("article must cite the verified primary source", engine.validate_draft(article, urls, {"https://brand.example/official"}))

    def test_search_console_export_identifies_a_real_query_opportunity(self) -> None:
        queries = Path(self.temp.name) / "Queries.csv"
        pages = Path(self.temp.name) / "Pages.csv"
        queries.write_text("Top queries,Clicks,Impressions,CTR,Position\nAmaron campaign,4,200,2%,9.4\n", encoding="utf-8")
        pages.write_text("Top pages,Clicks,Impressions,CTR,Position\nhttps://mkrting.com/campaigns/amaron/,4,200,2%,9.4\n", encoding="utf-8")
        output = seo_report.report(seo_report.rows(queries, ("top queries",)), seo_report.rows(pages, ("top pages",)))
        self.assertIn("Amaron campaign | 200 | 4 | 2.0% | 9.4", output)


if __name__ == "__main__":
    unittest.main()

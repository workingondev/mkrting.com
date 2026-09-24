# India-first source discovery plan

Research date: 23 September 2026. This document distinguishes an endpoint advertised or observed on the web from a feed successfully fetched and parsed by the Linux collector. Network name resolution is unavailable to this workspace, so the expanded feeds have **not** been live-tested from the laptop. Run `python3 tools/engine.py collect` and then `python3 tools/engine.py feeds` on a connected machine before calling any new feed operational.

## 1. Publisher leads

The operational feed registry is in `data/feeds.json`. It currently has 55 RSS/XML feed URLs, 12 enabled and 43 held for laptop verification or access review. The broader editorial registry is in `data/sources.json`: 97 sources and source classes, each with a region, role, specialty, collection route and activation state. Only the 12 enabled RSS feeds are active. The remaining entries are research candidates or held feeds, not live collectors or verified evidence. Run `python3 tools/probe_feeds.py` on the connected laptop to test the held feeds; `--activate` enables only feeds that parse and contain at least one relevant lead.
Incoming leads receive a local advertising, branding, startup, media or general-marketing label from their title and short summary. These labels are approximate and are not published as factual conclusions. Startup headlines can now enter the queue when they mention funding, founders, venture capital, acquisitions, D2C, go-to-market, product-market fit or unit economics.

| Publisher | Route and decision | Best use |
| --- | --- | --- |
| [Marketing Mind](https://marketingmind.in/feed/) | Main RSS enabled; do not depend on guessed category feeds | India campaigns, branding and startup leads |
| [afaqs!](https://www.afaqs.com/rss) | RSS enabled | Indian creative and agency coverage |
| [Social Samosa](https://www.socialsamosa.com/rss) | RSS enabled | Social campaigns and case-study leads |
| [MediaNews4U](https://www.medianews4u.com/feed/) | RSS enabled, medium editorial priority | High-volume launches; require more original evidence |
| [ET Brand Equity](https://brandequity.economictimes.indiatimes.com/rss) | Marketing, Advertising, Recent and Media feeds enabled; Digital and Research held pending runtime checks | Brand and business context; duplicate category URLs are deduplicated |
| [Marketing Dive](https://www.marketingdive.com/feeds/news/) | RSS enabled | Select global stories with a transferable lesson |
| [Design Week](https://www.designweek.co.uk/feed/) | RSS enabled | Identity, packaging and design work |
| [YourStory](https://yourstory.com/feed) | RSS URL returned RSS content on 24 September; enabled, pending laptop collection check | India founders, consumer brands and startup operating context |
| [TechCrunch](https://techcrunch.com/feed/) | Publisher feed URL returned RSS content on 24 September; enabled, pending laptop collection check | Global startup and product context; select India-relevant or transferable stories |
| [Inc42](https://inc42.com/startups/) | Startup category feed reported by a feed directory; disabled pending permitted laptop fetch and parse | India startup ecosystem and business-model leads |
| [Adweek](https://www.adweek.com/feed/) | Disabled after feed redirect to another service in the web check | Global campaigns, via permitted access or newsletter |
| [Campaign India](https://www.campaignindia.in/rss) | Publisher advertises RSS, but automated access was restricted in the web check; disabled | Creative work; use newsletter or normal manual links for now |

The [Campaign India RSS page](https://www.campaignindia.in/rss) and [ET Brand Equity RSS directory](https://brandequity.economictimes.indiatimes.com/rss) document their routes. For Exchange4media, Storyboard18, The Drum, The Branding Journal, Ads of the World, The Brand Identity and Little Black Book, first establish a permitted feed or newsletter route. Do not infer an RSS endpoint from a site's name or crawl restricted pages to meet a source-count target.

A successful feed fetch still does not prove the feed is useful: inspect the first week of titles for appointment news, sponsored launches, duplicate rewrites and actual campaign assets. Disable a feed that adds noise or blocks collection. The collector stores feed title, URL and short summary as leads; it does not copy full articles. Added startup topics increase discovery, not permission to reproduce publisher text.

A concrete September 2026 example is [MediaNews4U's report on Canva's “Aap Aur Canva, Jodi Wah Wah!” campaign](https://www.medianews4u.com/canva-brings-farah-khan-raghu-ram-and-terence-lewis-together-for-new-india-campaign/). It is now in the local queue as cluster 10. The report suggests an interesting creative mechanism, but the cluster is **held** until current official Canva/Fundamental material and independent corroboration are checked. [Canva's older India campaign page](https://www.canva.com/en_in/newsroom/news/india-brand-campaign/) concerns “Dil Se, Design Tak” and must not be passed off as the primary source for this new work. This illustrates why lead collection and evidence collection are separate.

## 2. Original evidence before writing

For each promising lead, seek an official campaign film, brand newsroom post, agency case study, product/identity launch page, or attributable first-person statement. Maintain a small human-verified watchlist of relevant Indian brands and agencies. Initial organizations to review include Amul, Cadbury India, Zomato, Swiggy, Blinkit, Zepto, CRED, boAt, Ogilvy India, DDB Mudra, FCB India, Talented and Schbang. Their inclusion here does **not** mean their channels have been verified or wired into the collector.

When a brand has an identifiable official YouTube channel, its channel ID can be used with the [YouTube Atom feed format](https://developers.google.com/youtube/v3/guides/push_notifications). Verify ownership and ID before adding it. A video is evidence of the creative itself, but a claim about agency credits or campaign results may need another source. Add verified original URLs through `engine.py add --primary --cluster ID` and a separate independent report through `engine.py add --cluster ID`. The collector only retains feed metadata: title, URL, short summary and dates, not full copied publisher articles.

## 3. Other discovery routes, in order

1. **Manual social intake now:** add a URL, a descriptive title and why it looks interesting with `engine.py add`. Instagram, LinkedIn and X links are leads, not automatically primary sources.
2. **Official channels next:** verify brand/agency sites and YouTube channel IDs one by one, then add their feeds or a small permitted sitemap/newsroom monitor. Check robots and access rules.
3. **Google News RSS experiments:** test focused India queries such as “Indian startup rebrand” and “India brand film” on the laptop. Record reliability and duplication before enabling them. News results still need first-party evidence.
4. **Newsletter intake later:** use a dedicated research mailbox only after it exists and has consent-based subscriptions. Extract links and subjects, avoid storing whole copied newsletters. Exchange4media, Storyboard18 and Campaign India are candidates.
5. **Instagram later:** use approved Meta access or a licensed social-listening provider if the extra coverage justifies it. There is no unlimited free official substitute for arbitrary account scraping.

None of routes 2–4 is currently implemented as an automatic collector. The practical launch path is publisher RSS plus manual first-party evidence and manual social leads.

## 4. Selection and AI workflow

The local score is an inexpensive **shortlist heuristic** based on India relevance, recency, campaign-like wording and presence of a marked primary source. Multiple feeds from the same publisher count as one source group; a second group adds only a small signal. It does not measure originality, creative quality or commercial impact. Before a draft, the system now requires a first-party source and reporting from a different domain. Gemini's first call receives only these supplied URLs and short notes; it must list each claim with an exact supplied source URL, medium/high confidence, unknowns and a strategic angle. Unsourced claims hold the dossier. The second call writes an original analysis from that ledger, with a concrete reader question and lesson.

## Source network expansion

The source registry separates discovery leads from first-party evidence, independent reporting, creative archives, branding, strategy, effectiveness, consumer data, distribution, creator/social, adtech, startups, awards and research archives. These roles are editorial routing hints; they do not certify the reliability of an individual article. Use `python3 tools/engine.py sources` to inspect the registry. `tools/build_source_registry.py` rebuilds it from the current RSS list and reviewed watchlist.

The watchlist includes Indian trade publishers (BestMediaInfo, Agency Reporter, IMPACT, Pitch, Exchange4media and others), global campaign libraries (Little Black Book and Ads of the World), identity and packaging sources (Brand New, Transform Magazine, BP&O, DIELINE and others), and award records (Kyoorius, ABBY, Cannes Lions, Effies, D&AD, Clio and The One Show). [Agency Reporter describes its adtech and CTV focus](https://agencyreporter.com/contact-us/); [WARC describes its strategy and effectiveness library](https://www.warc.com/strategy). The latter is a manual or licensed research reference in our registry; no paywalled text ingestion is configured.

Before activating any watchlist source: verify the official site and exact endpoint, check robots and terms, test a single permitted metadata fetch, classify whether the item is original reporting or a rewritten release, then monitor useful leads and failures. `sitemap_diff`, `search_monitor`, `database_monitor`, `newsletter_ingest`, `manual_or_paid` and `youtube_channel_rss` describe possible routes; they are **not implemented collectors**. An official brand or agency URL must be verified for each particular campaign. An award listing establishes a specific award or credit, not sales impact.

Store headline, URL, source and dates at discovery time. Fetch bounded source text only when preparing a promising dossier. Future metadata fields such as author, OG image, agency and embedded video should be added only when a permitted collector and clear provenance exist; the current database does not yet populate them. The next functional step is a small sitemap monitor with per-source access checks and a one-week quality review, followed by a campaign and agency credit model. Avoid increasing source volume simply to reach a numeric target.

The PR includes the draft, source list, claim ledger, unknowns, selection angle, media-rights note and an AI-check status. **No independent sentence-by-sentence AI verification exists yet.** The status says so; the human editor must compare every factual sentence with the sources, including sentences omitted from the ledger. A third separate verifier can be added after the real Gemini integration is tested and its cost and false-clearance rate are measured. It would support, not replace, review.

Publish the strongest useful story even if it is the only one that day. The cap is three candidate drafts per India day; there is no automatic publication quota. Avoid near-rewrites of trade reports and unsupported claims of virality or sales. Google's [spam policy](https://developers.google.com/search/docs/essentials/spam-policies) warns that republishing scraped or lightly transformed material without substantial added value can be abusive.

## 5. Activation checks

- On the connected Linux laptop, collect once and inspect `engine.py feeds`; retain only feeds that parse and produce useful leads. Recheck after publisher changes.
- Verify official channels and add them to an evidence watchlist before automating any new fetcher.
- Supply a Gemini key and test one low-risk dossier; review source retrieval, token usage and the resulting claim ledger.
- Supply the GitHub repository later and inspect a draft PR end to end. Enforce human review and passing build checks before merge.
- Confirm the user timer with `systemctl --user list-timers mkrting-cycle.timer` and logs. Timer files and a lingering marker are present, but this session could not query the user bus. A sleeping or disconnected laptop will not collect new stories.

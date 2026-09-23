# Research and operating method

## Editorial position

Publish three formats when evidence supports them: quick sourced campaign brief, deeper teardown, and evergreen startup playbook. A daily target of three is operational capacity, never a reason to publish thin copy. Reviews, corrections and source labels are part of the product.

## Source system, in order

1. **Discovery:** Publisher RSS feeds and manually submitted links are the launch path. Approved Meta Business Discovery is optional. These are leads, not facts to repeat.
2. **Original evidence:** Brand campaign page, brand/agency release, official video, original creative or other first-party material. Verify ownership and relevance to the specific campaign.
3. **Corroboration:** An independent trade report or another reliable source domain for credits, dates, context and competing interpretations. Curator accounts may be sponsored; check disclosures.
4. **Research ledger:** Record each claim with a supporting URL, confidence and unresolved questions. Hold the article when important details cannot be verified.
5. **Original analysis:** Explain the audience tension, strategic choice, execution and transferable lesson. Label interpretation. Do not treat views, likes or press coverage as evidence of sales or effectiveness.
6. **Review:** Check factual claims, brand/agency credits, headline, tone, original creative link, copyright/embedding rights and disclosures in a draft PR. Only merge approved work.

The local scoring system values recency, an Indian angle, multiple source domains and a first-party source. It does not equate popularity with quality. Similar headlines are grouped before AI is called. The current version requires an original source and independent reporting from another domain before Gemini drafting. The automated Meta connector is optional; editors can add verified first-party URLs from brand and agency sites. No Instagram private-page scraping, session-cookie automation or media downloading is used. See the [source expansion plan](source-discovery-plan.md) for the publisher-by-publisher decisions and unfinished collection routes.

## Instagram watchlist audit

The 100-row watchlist deliberately includes publishers, agencies, brands and D2C companies. These are **research candidates** selected for relevance to campaign discovery, not a claim that all are active, high quality or accessible through Meta. The audit fetched each organization's public homepage where robots.txt allowed it and looked for its Instagram link. On the first pass, 46 homepages contained an Instagram-like link; 35 rows were promoted to `verified` after selecting the correct organization/region account. Eleven showed no link, 21 were skipped by robots checks, and 22 failed to load within the audit limits. Four more accounts were checked against official material after the audit, bringing the verified total to 39. False links such as embed scripts were excluded from promotion. Re-run `python3 tools/verify_instagram.py` and review the JSON before changing `status` in the CSV.

Examples in the verified group include Marketing Mind, Mad Over Marketing, Social Samosa, afaqs!, Campaign India, Exchange4media, ET Brand Equity, Storyboard18, WATConsult, Creativeland Asia, Zomato and Paper Boat. The full registry contains 100 names and per-row verification URLs. The API may still be unable to access a verified account if it is not a professional account or the app lacks permission. A link on a company's homepage establishes account association; it does not endorse every post or make it a primary campaign source.

## AI budget and publishing logic

- RSS and Meta collection, basic filtering, URL cleanup, grouping and ranking use local code and SQLite.
- Gemini is invoked only for an eligible lead: one bounded research call with supplied source URLs, then one article JSON call. The research ledger must contain claims linked to supplied URLs. The project limits calls and total observed tokens per India day. Model prices and free-tier limits change, so adjust caps against the live Google console before enabling paid use.
- Draft validation checks mandatory fields, source URLs, dates, length and risky performance language. It cannot prove that every sentence is true. The PR labels the AI check as not independently verified and includes the claim ledger, unknowns and media-rights note. The PR checklist and human review remain necessary.
- The timer may find zero eligible stories on some days. It will not synthesize a quota from unverified social posts.
- A merged article becomes a static page. The laptop can be offline while the published site remains available; the laptop must be online for collection and new PRs.

## SEO and growth

The build emits clean paths, readable HTML, mobile styles, title/description/canonical tags, `Article` JSON-LD on stories, an XML sitemap and RSS. Publish useful original analysis consistently; link campaign pages internally from relevant topic hubs as the archive grows. Once live, verify the domain in Google Search Console, submit the sitemap and inspect indexing/errors and search queries. Add author bios and a working corrections address before scaling. No technical feature guarantees a global ranking. Expand topic clusters around India brand strategy, campaign teardowns, packaging, identity and startup distribution only when there is enough original material to make each page useful.

## Source links reviewed during research

- [Meta Instagram API guide](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api) and [Business Discovery reference](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery/)
- [Meta on unauthorized scraping](https://www.facebook.com/help/463983701520800)
- [Google Gemini models](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [pricing](https://ai.google.dev/gemini-api/docs/pricing) and [URL context](https://ai.google.dev/gemini-api/docs/generate-content/url-context)
- [Google helpful content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [AI-generated content guidance](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content) and [Article markup](https://developers.google.com/search/docs/appearance/structured-data/article)
- [GitHub Pages deployment source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Robots Exclusion Protocol, RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) and [India Copyright Act exceptions](https://copyright.gov.in/Exceptions.aspx/FORMXV/FORMXV/Society/Documents/Documents/ObjectedApplication.aspx)

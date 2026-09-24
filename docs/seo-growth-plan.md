# Search growth plan for mkrting.com

Updated: 24 September 2026. This is a working editorial plan, not a promise of a ranking. The public `https://mkrting.com/` site is live with eight articles and two guides. The owner reports that Search Console shows no performance or indexing data yet, so keyword positions, organic traffic and field Core Web Vitals cannot be measured. The next milestone is confirming Google discovers and indexes the canonical pages.

## 1. Win a defined audience before a broad word

“Marketing” and “branding” are very broad queries. Current results for related informational searches include established sites such as [Shopify's branding guide](https://www.shopify.com/blog/what-is-branding) and [Coursera's marketing strategy guide](https://www.coursera.org/articles/marketing-strategy). A new one-article domain should start with questions where it can contribute a specific answer: the strategy behind an identifiable Indian campaign, the role of a product feature in a creative idea, or a usable campaign-analysis method. This is an inference from the observed results, not a measured keyword-volume claim.

Initial search-intent map:

| Reader question | Page type | Current action |
| --- | --- | --- |
| How do I analyse a marketing campaign? | Evergreen field guide and worksheet | Built at `/guides/campaign-analysis/` |
| What can Indian startups learn from recent campaigns? | Curated lessons hub after enough examples | Do not create an empty hub |
| How do Indian brands turn product truths into advertising? | Comparative analysis based on several sourced campaigns | Research once the archive exists |
| What changed in Indian packaging or identity design? | Sourced design teardown with original diagrams | Research and publish when an original example is verified |

The campaign analysis guide is live. Check the live search results again before assigning an article to a query; the intent and competing pages change. Do not turn every synonym into a near-duplicate page.

## 2. Make each article earn its URL

Before a PR is merged, an editor should be able to answer:

1. What real reader question does this page answer? The draft stores `reader_question`.
2. Does the visible headline name the campaign or brand clearly? Does the opening paragraph identify the work immediately?
3. What fact or firsthand observation is here that a news rewrite would not add? The original creative, a sourced comparison, a decision diagram or an interview can provide that value.
4. Can every factual claim be traced to a source? Is the strategic interpretation explicitly an interpretation?
5. Are outcomes supported by an appropriate measurement source, rather than views, likes or publicity alone?
6. Does the image add understanding, have permission to be used, and have descriptive alternative text?
7. Is there a useful next page to link to, such as the analysis guide or a closely related campaign?

The draft engine now asks Gemini for one `reader_question`, a descriptive `seo_title`, and a summary `seo_description`. The PR and build reject missing fields. These are editorial aids. Google may generate its own result title and snippet, so there is no fixed character count that guarantees display. We use a separate search title only when it accurately represents the visible page. [Google's title guidance](https://developers.google.com/search/docs/appearance/title-link) recommends distinctive, descriptive titles and alignment with prominent on-page text.

Use the same URL for meaningful updates; change the visible update date and sitemap `lastmod` only when the content, sources, structured data or important links substantially change. Do not refresh dates to simulate newness. [Google's sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) explicitly expects verifiably accurate modification dates.

## 3. Build a navigable archive

The current architecture is `/campaigns/` and `/guides/`. The builder opens `/india/` and `/teardowns/` only after each has at least three articles. Individual articles link to the campaign archive, relevant further reading and the field guide. As the archive grows, group articles around real reader tasks such as Indian campaign strategy, packaging design, brand positioning and startup distribution. Write a useful introduction and choose the best examples for each new hub. Only publish a hub when it has enough distinct material to help a visitor.

Avoid auto-generated tag pages with the same card list and a swapped keyword. Those pages can create duplication and weak search results. Maintain one canonical URL per article. If an article changes slug, add a redirect from the old URL when the hosting setup permits it, update internal links and the sitemap, and verify the redirect before removing the old page. Do not create regional English copies solely to capture country keywords. If genuine Hindi or other translations are later commissioned, review them and add correct language links then.

## 4. Technical launch sequence

1. Confirm `https://mkrting.com/` is the production domain and `www.mkrting.com` redirects to it. The sitemap, robots file and main page have previously returned HTTP 200; recheck after major deployments. `trailingSlash: true` matches generated canonicals. [Google technical requirements](https://developers.google.com/search/docs/essentials/technical). See the [Vercel launch guide](vercel-launch.md) for exact checks.
2. In the verified domain property in Google Search Console, submit `https://mkrting.com/sitemap.xml`, inspect the homepage, guide and an article, and use **Test live URL** before **Request indexing**. A submitted sitemap is a discovery hint, and an empty report does not prove a technical fault. Check again after Google has had time to crawl. [Search Console setup](https://developers.google.com/search/docs/monitor-debug/search-console-start).
3. Test the article and breadcrumb markup with Google's Rich Results Test after deployment. Schema must reflect visible content; it makes a page easier to understand but does not guarantee a rich result. [Article guidance](https://developers.google.com/search/docs/appearance/structured-data/article), [breadcrumb guidance](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb).
4. Measure real mobile performance with Search Console and PageSpeed Insights after traffic arrives. Google recommends LCP within 2.5 seconds, INP under 200 ms and CLS under 0.1. The static site has no client JavaScript, but no field-data score has been measured. [Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals).
5. Give substantive articles relevant original visuals where they genuinely help explain the work. For Discover, Google recommends high-quality, crawlable images at least 1200 px wide and permits `max-image-preview:large`; eligibility is not guaranteed. [Discover guidance](https://developers.google.com/search/docs/appearance/google-discover).
6. Once the domain is live, consider IndexNow for Bing and participating engines when URLs change. It requires a key file hosted on the live domain. It is a discovery notification, not a ranking service and not a substitute for Google's Search Console. [Bing IndexNow setup](https://www.bing.com/indexnow/getstarted).

For Google's AI Overviews and AI Mode, use the same foundation: an indexable page with a useful, original answer and clear evidence. Google says there is no special schema, file or separate submission for these features. Track any resulting visits within Search Console's Web performance data; it does not provide a guaranteed placement. Avoid selling or building a separate “AI SEO” shortcut. [Google's AI features guidance](https://developers.google.com/search/docs/appearance/ai-features), [generative AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

## 5. Backlinks that a publication can earn

Links help discovery and can indicate that someone found an article useful. The objective is to make journalists, educators, founders and agencies *want* to cite a specific piece of work. No outreach should ask for a link as a condition of coverage.

| Asset or relationship | Why someone might link | First practical step |
| --- | --- | --- |
| Campaign analysis worksheet | A teacher, student or marketer can reuse the method | Share the public guide where the question is already being discussed |
| Original campaign comparison | A journalist can cite a transparent finding across several campaigns | Review 20–30 verified examples, publish criteria and limitations |
| Brand/agency source acknowledgments | Credited teams may share a careful interpretation | After publication, send the article for factual review or awareness without requesting a link |
| Expert interviews | Interviewees and their communities may share substantive insight | Ask one clear question, publish the full context and attribution |
| Relevant editorial contributions | Another publisher's audience gets an original answer | Pitch a unique argument or dataset, not a recycled promotional post |
| Legitimate profiles | Readers can discover the publication from its own channels | Link from the company's real social profiles and newsletter |

Do not buy followed links, use private blog networks, mass-submit directories, auto-post forum comments, run link exchanges or distribute keyword-stuffed guest posts. If a link is paid or sponsored, qualify it appropriately. These are not shortcuts: [Google's link-spam policy](https://developers.google.com/search/docs/essentials/spam-policies) covers paid links and automated link creation. Backlink work can begin after the live URL exists; no outreach has been sent from this project.

## 6. Run the learning loop

After launch, review Search Console by **query and landing page**, split at least by India versus other countries and mobile versus desktop when data permits. Track indexed canonical pages, impressions, clicks, CTR and average position alongside the actual page's quality and referral traffic. Average position is a noisy aggregate; use it to find questions, not to declare a win from a small fluctuation. [Search Console performance guidance](https://developers.google.com/search/docs/monitor-debug/search-console-start).

Each month:

- Export the Queries and Pages CSV tables for the same time period and run `python3 tools/seo_report.py --queries Queries.csv --pages Pages.csv`. It writes a review list to `.local/seo-report.md`.
- Inspect high-impression queries where the site appears but the page does not fully answer the question. Improve that page with evidence or clearer structure, then monitor it over several weeks.
- Check which pages are excluded from indexing, what canonical Google selected, and whether any structured-data errors appeared.
- Review relevant referring links and mentions. Correct attribution errors; do not chase a target number of backlinks.
- Retire or consolidate weak pages if they duplicate stronger ones. Keep their URLs redirected when appropriate.

## 7. Ninety-day sequence after the domain goes live

| Period | Work | Evidence of progress |
| --- | --- | --- |
| Days 1–14 | Deploy; verify domain, sitemap, canonical host, Search Console and Bing; test core pages | Public URLs accessible and submitted; indexing status visible |
| Days 15–45 | Publish a small set of genuinely distinct India-first teardowns and one more evergreen guide; distribute each to relevant readers | First query and page impressions; feedback on usefulness |
| Days 46–75 | Build one original comparison or dataset from verified campaigns; publish methodology; begin selective editorial outreach | Independent mentions or citations, qualified referral visits |
| Days 76–90 | Use query/page data to improve the best opportunities; consolidate overlap; test mobile experience | More relevant indexed pages, growing qualified clicks and returning readers |

The sequence is a work plan, not a traffic forecast. A site can meet every technical requirement and still take time to appear in results. [Google Search Essentials](https://developers.google.com/search/docs/essentials) makes clear that eligibility is not a ranking guarantee.

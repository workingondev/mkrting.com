# mkrting.com

An India-first marketing and brand strategy journal, plus a local editorial discovery system. The public site is static and built for **Vercel**. A Linux laptop gathers public leads, groups duplicates, prepares evidence-led drafts with Gemini, and opens **draft GitHub pull requests**. A person checks and merges each article; Vercel builds and deploys the public frontend from `main`.

## What is ready

- Responsive homepage, article, campaign, guide, about, method and corrections pages. India and teardown hubs appear once each has enough distinct articles.
- Five prelaunch analyses covering  Flipkart, Amazon, Jio and Zomato, plus a campaign-analysis worksheet. Each article includes primary evidence and independent reporting, source links, article and breadcrumb schema, canonical URLs, sitemap, robots.txt and RSS. See [launch story review](docs/launch-story-review.md) for the claim-by-claim editorial handoff.
- A 14-endpoint source registry, with 10 RSS endpoints enabled for collection. It now includes Marketing Mind, afaqs!, Social Samosa, MediaNews4U, selected ET Brand Equity feeds, Marketing Dive and Design Week. Endpoint format was checked through the web research tool; live collection from this Linux workspace could not be tested because network name resolution is unavailable here. The collector records each feed's actual run status.
- Instagram is optional. The 100-account file is a manual research watchlist, not a working feed or a launch dependency.
- Local SQLite collection, relevance filter, duplicate grouping, source scoring, explicit primary-evidence gate, capped Gemini research/writing, local drafts, draft PR creation and Linux timer.
- Site build and link check on PR; Vercel preview deployments on branches and production deployment from `main` after the repository is connected.

## Start locally

Python 3.10+ is enough; the core uses the standard library.

```bash
python3 tools/build_site.py
python3 tools/check_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open `http://localhost:8765/`. For collection:

```bash
python3 tools/engine.py collect
python3 tools/engine.py feeds
python3 tools/engine.py shortlist
python3 tools/engine.py usage
```

The local database and drafts are in `.local/` and are ignored by Git. No key is needed to collect and shortlist. `feeds` shows the last runtime result for every enabled source. A listed endpoint is not counted as working until the laptop records a successful fetch and parse.

## Enable the editorial cycle

1. Copy `.env.example` to `.env`. Add a Gemini API key. Set a daily call/token cap you are comfortable with. Never commit `.env`.
2. Run `python3 tools/run_cycle.py` once and inspect the report. It collects feeds, optionally collects Meta posts, drafts at most three **eligible** stories per India calendar day, and optionally opens draft PRs.
3. On a Linux machine using systemd, run `python3 tools/install_timer.py`. This installs a user timer for this checkout and checks every four hours. Inspect with `systemctl --user list-timers mkrting-cycle.timer` and `journalctl --user -u mkrting-cycle.service -n 100`. A machine that should keep running after logout needs user lingering enabled by its administrator. The timer files and lingering setting exist on this machine, but their current running status could not be queried in this session. Collection stops while the laptop sleeps or loses connectivity.
4. To create PRs, set `GITHUB_OWNER`, `GITHUB_REPO` and a fine-grained `GITHUB_TOKEN` with repository **Contents read/write** and **Pull requests read/write**. Use a dedicated account/token with the smallest necessary scope. The script cannot merge PRs.
5. Instagram is an optional later connector. If you obtain approved Meta access for your own professional account, set `META_ACCESS_TOKEN`, `META_IG_USER_ID` and a currently supported `META_API_VERSION`. The connector only uses rows marked `verified`, rotates through up to 20 per run, and never downloads media. RSS collection and manual lead entry do not depend on it.

To add original evidence manually to a lead:

```bash
python3 tools/engine.py add --cluster 12 --url 'https://brand.example/campaign' --title 'Official campaign page' --source 'Brand' --primary
python3 tools/engine.py draft 12
```

Only mark a source `--primary` after checking that it is controlled by the brand or credited agency and actually documents this campaign. A separate source domain is also required.

To add a campaign seen on social media without an Instagram API, use the same command without `--primary`, including a short reason in `--summary`:

```bash
python3 tools/engine.py add --url 'https://www.instagram.com/p/EXAMPLE/' --title 'Brand campaign worth investigating' --source 'Manual social lead' --summary 'Potentially useful brand-positioning example; find official creative and independent reporting'
```

The URL becomes a lead only. The system will hold drafting until a verified first-party campaign source and independent reporting are added to the same cluster.

## Vercel, GitHub and launch

See the [Vercel launch guide](docs/vercel-launch.md) for the exact project settings, domain steps, analytics setup and live SEO checks. The tracked [vercel.json](vercel.json) builds the Python-generated HTML into `dist/`; Vercel serves only that directory. The collector, Gemini key and local database stay on the Linux laptop. The GitHub workflow is now validation only; it does not deploy to GitHub Pages.

The Vercel CLI is installed in the ignored local folder `.local/vercel-cli/`; run `.local/vercel-cli/node_modules/.bin/vercel --version` to check it. Connecting it to your Vercel account is a separate step described in the launch guide.

Put this project in a GitHub repository with a `main` branch, import it into Vercel, and set `main` as the production branch. Add both `mkrting.com` and `www.mkrting.com` to the Vercel project, with `www` redirecting to the apex domain used by the existing canonical tags and sitemap. Protect `main` with a required pull-request review and the build check. Draft PRs must be marked ready and reviewed before merge.

The project cannot complete this external setup without the repository, Vercel project access and domain access; the automated editorial cycle also needs the Gemini key. Meta credentials remain optional. The site and local collector work before those are supplied. Three daily posts are a **ceiling**, not a guaranteed volume: the system holds stories when evidence or API budget is insufficient.

## Editorial rules

See [Research and operating method](docs/research-and-method.md) and the [source expansion plan](docs/source-discovery-plan.md). The key rule is simple: Instagram and trade headlines are discovery signals. The article must cite the original creative or brand/agency source, identify what is interpretation, and avoid unsupported success claims. Linking and credit do not permit copying another publisher's text or campaign images. The draft PR now carries the AI research claim ledger, open questions, image-rights status and a clear notice that article-level fact checking remains for the editor.

## Search growth

See the [SEO growth plan](docs/seo-growth-plan.md) for the search-intent map, technical launch checks, original content priorities, backlink approach and monthly Search Console review. The article draft gate now requires a reader question, a descriptive search title and a useful summary. After launch, exported Search Console Queries and Pages tables can be reviewed with `python3 tools/seo_report.py --queries Queries.csv --pages Pages.csv`.

## Important files

| Purpose | File |
| --- | --- |
| Public site builder | `tools/build_site.py` |
| Collector, ranking, Gemini writer | `tools/engine.py` |
| Optional Meta collector | `tools/meta_collect.py` |
| Draft PR creator | `tools/create_pr.py` |
| Linux cycle | `tools/run_cycle.py` |
| Feed registry | `data/feeds.json` |
| Instagram research registry | `data/instagram_watchlist.csv` |
| Site content | `content/articles/` |
| Vercel build and URL rules | `vercel.json` |
| Vercel domain, analytics and SEO checklist | `docs/vercel-launch.md` |

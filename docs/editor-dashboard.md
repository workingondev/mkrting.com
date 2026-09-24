# Local editorial desk

Open **mkrting Editorial Desk** from the Linux application menu. It starts the private dashboard on the laptop and opens it in the browser. The desk uses `http://127.0.0.1:8766/`; it is not deployed to Vercel. API keys stay in the laptop's `.env`.

While the desk process is running, it checks enabled RSS feeds about every two hours. The **Check sources now** button also starts a collection immediately. Closing the browser tab does not stop the local desk process; restarting the laptop stops it. The desk does not draft or publish stories without your clicks.

## Daily flow

1. Open a story in **Story queue**. Scores help prioritize; they do not prove that a story is accurate.
2. Click **Find evidence + create AI draft**. The desk checks the report's links and the likely brand website and sitemap for an original campaign page. If it finds official evidence, it drafts from that plus reporting. Otherwise Gemini creates a clearly attributed reported analysis from the collected report. If the article page is not machine-readable, it may use a substantive RSS summary instead and explicitly disclose that limitation. The editor must open the linked full article and verify every fact before approval. If even the feed summary is too thin, the desk holds the story and shows the reason.
3. Open the article in **Drafts**. Read the complete text and open its evidence links. Check facts, dates, wording, image rights, and any open questions.
4. Click **Create draft PR** if you want to review it on GitHub first. When satisfied, tick the review confirmation and click **Approve & publish**. The desk creates or updates the PR, waits for the GitHub build check, merges the PR, and Vercel begins its production deployment.

A repository-scoped GitHub token needs **Contents: read/write**, **Pull requests: read/write**, and **Checks: read**. Branch protection can require another reviewer; the desk shows a blocked merge rather than bypassing it. A successful merge starts deployment, but the live page may take longer to appear.

This Gemini API project has zero Gemini 3 Search grounding quota, and the Gemini 2.5 models reject new users. The desk does not call Gemini's web search. It uses site and feed discovery without another API key. Article research and writing use `GEMINI_MODEL` and `GEMINI_FALLBACK_MODELS`. AI drafts remain subject to human review. The desk holds stories when the collected report is unreadable, too thin to support an original analysis, or Gemini capacity is unavailable. It does not guarantee a fixed number of daily articles.

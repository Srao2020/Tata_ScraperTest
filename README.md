# Tata Scraper Test

This repository is a set of workflows for collecting AI news or article content and turning it into structured reports for a Tata Capital AI product use case.

Most of the projects revolve around the same core idea:

1. Gather source material.
2. Convert that source material into a prompt.
3. Send the prompt to Groq.
4. Save the final written output.

The folders represent different ways of doing that, with different tradeoffs in speed, depth, reliability, and amount of manual input.

## Repository Structure

```text
Tata_ScraperTest/
├── api_config.py
├── .env.example
├── APITest/
├── Headings/
│   ├── OnlyHeadings/
│   └── WholeArticle/
└── Agent/
    ├── AgentCall/
    └── MultiScraper/
```

## Shared Building Blocks

### `api_config.py`

Stores shared API keys used by the scripts.

What it does:
- Provides `GROQ_API_KEY` for Groq-based report generation.
- Provides `NEWS_API_KEY` for the NewsAPI workflow in `APITest`.

Pros:
- Simple shared configuration for all scripts.
- Easy to reuse across multiple folders.

Cons:
- Keeps secrets in a Python file, which is convenient but less safe than environment variables or a secret manager.
- Makes local setup easy, but is not ideal for production or team sharing.

### `.env.example`

Documents the environment variables the repo expects.

What it does:
- Acts as a setup reference for API keys.

Pros:
- Useful for onboarding.
- Better long-term pattern than hardcoding keys.

Cons:
- The current scripts rely mainly on `api_config.py`, so the environment-variable path is only partly standardized across the repo.

## Project Overview

### `APITest/`

This is the metadata-driven weekly news workflow.

Main files:
- [news_weekly_update.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/news_weekly_update.py)
- [README.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/README.md)
- [outputs/weekly_update.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/outputs/weekly_update.md)

What it does:
- Pulls AI news from NewsAPI for a time window.
- Deduplicates articles by URL.
- Keeps only article metadata and short snippets.
- Builds a weekly synthesis prompt for Groq.
- Saves one weekly markdown report.

Process:
1. Query NewsAPI using a fixed AI-focused search string.
2. Collect title, publisher, URL, publish date, description, content snippet, and author.
3. Trim long fields to keep the prompt manageable.
4. Insert the news pack into a weekly prompt template.
5. Send the prompt to Groq and write the final report.

Pros:
- Fastest path to a weekly overview.
- No browser automation required.
- Scales better than full-page scraping because it works on API responses only.
- Good for broad trend monitoring across many articles.

Cons:
- Limited by NewsAPI coverage and snippet quality.
- Does not fetch full article text.
- Can miss nuance that only appears in the body of the article.
- Depends on query quality; weak queries can miss relevant news or include noise.

Best for:
- Quick weekly intelligence summaries.
- Situations where breadth matters more than article depth.

### `Headings/OnlyHeadings/`

This is the lightweight browser-scraping workflow for a single article.

Main files:
- [scraper.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/OnlyHeadings/scraper.py)
- [browser_fetch.js](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/OnlyHeadings/browser_fetch.js)
- [package.json](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/OnlyHeadings/package.json)
- [README.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/OnlyHeadings/README.md)

What it does:
- Opens an article in a real browser with Playwright.
- Extracts title, metadata, headings, and subheadings.
- Avoids scraping the full body text.
- Sends the reduced structure to Groq for analysis.

Process:
1. Use Node + Playwright to load the page in Chromium or a local browser.
2. Return rendered HTML to Python.
3. Parse visible structure with `HTMLParser`.
4. Keep `title`, `h1`/`h2`, `h3`-`h6`, and selected meta tags.
5. Build a reduced prompt and send it to Groq.
6. Save one final markdown output.

Pros:
- More reliable than plain HTTP scraping for JavaScript-heavy pages.
- Much smaller prompt than full-article mode.
- Preserves article structure, which helps infer the main topics quickly.
- Lower token usage than full-text scraping.

Cons:
- Can miss critical detail that appears only in paragraphs.
- Headings alone may oversimplify the article.
- Browser automation adds setup and runtime overhead.
- Still depends on page HTML quality; weak heading structure reduces usefulness.

Best for:
- Fast article triage.
- Cases where structure matters more than exact wording.
- Lower-cost experimentation with browser-based scraping.

### `Headings/WholeArticle/`

This is the deep single-article workflow.

Main files:
- [scraper.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/WholeArticle/scraper.py)
- [browser_fetch.js](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/WholeArticle/browser_fetch.js)
- [package.json](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/WholeArticle/package.json)
- [README.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Headings/WholeArticle/README.md)

What it does:
- Opens one article in a browser.
- Extracts metadata plus visible text blocks such as paragraphs, headings, list items, and blockquotes.
- Sends the fuller article payload to Groq.

Process:
1. Load the page through Playwright.
2. Return rendered HTML to Python.
3. Parse article text from tags like `p`, `li`, `blockquote`, and headings.
4. Remove obvious noise sources like scripts and styles.
5. Insert the full article payload into the prompt.
6. Send it to Groq and save the final output.

Pros:
- Richer source context than the headings-only version.
- Better for extracting nuance, evidence, and secondary details.
- More likely to capture the actual meaning of the article.
- Useful when the article body matters for strategic analysis.

Cons:
- Larger prompts mean higher cost and more room for noise.
- More likely to include navigation text or irrelevant page content if the page is messy.
- Slower than metadata-only or headings-only flows.
- Still not a site-specific parser, so extraction quality varies by publisher layout.

Best for:
- In-depth analysis of one important article.
- Comparing how much better full-text prompting performs than heading-based prompting.

### `Agent/AgentCall/`

This is the simplest Groq-only workflow.

Main files:
- [agent.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/agent.py)
- [README.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/README.md)
- [outputs/final_output.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/AgentCall/outputs/final_output.md)

What it does:
- Sends one fixed prompt directly to Groq.
- Does not fetch any sources itself.
- Produces a weekly-style report from the prompt alone.

Process:
1. Use a static prompt that lists preferred source types and output rules.
2. Send that prompt to Groq.
3. Save the response.

Pros:
- Smallest and easiest workflow in the repo.
- Useful for testing prompt shape, model behavior, and report formatting.
- No scraping or NewsAPI setup required beyond the Groq key.

Cons:
- No built-in source retrieval.
- Relies on the model to reason about sources from the prompt instructions alone.
- Least reproducible and least grounded workflow in the repo.
- Harder to verify source coverage and factual completeness.

Best for:
- Prompt prototyping.
- Quick experiments before adding source ingestion.

### `Agent/MultiScraper/`

This is the batch full-article workflow.

Main files:
- [scraper.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py)
- [browser_fetch.js](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/browser_fetch.js)
- [article_links.txt](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/article_links.txt)
- [package.json](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/package.json)
- [README.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/README.md)

What it does:
- Accepts multiple article URLs.
- Scrapes the full visible content of each article in a browser.
- Combines them into one weekly source pack.
- Sends the combined prompt to Groq for theme-based synthesis.

Process:
1. Read URLs from command-line arguments or `article_links.txt`.
2. Open each page with Playwright.
3. Extract title, metadata, and visible text blocks.
4. Build a combined weekly payload with all sources.
5. Send one synthesis prompt to Groq.
6. Save one combined final report.

Pros:
- Most complete source-grounded workflow in the repo.
- Good balance between manual curation and model synthesis.
- Better than `APITest` when source quality matters more than source count.
- Better than single-article flows when the goal is weekly theme detection.

Cons:
- Most operationally heavy workflow.
- Requires manual URL collection unless another system feeds it.
- Prompt size can grow quickly with many long articles.
- Extraction quality still depends on generic HTML parsing, so some publishers may introduce noise.

Best for:
- High-quality curated weekly reports.
- Comparing several important articles together.
- Use cases where article selection is manual and deliberate.

## Shared Process Patterns

### Browser-backed scraping

Used in:
- `Headings/OnlyHeadings`
- `Headings/WholeArticle`
- `Agent/MultiScraper`

What it does:
- Uses Playwright to render the page before extraction.
- Falls back across bundled Chromium, Chrome, Edge, or Chromium installs.

Pros:
- Better for JavaScript-rendered or protected pages.
- More realistic page rendering than a plain HTTP request.

Cons:
- Slower than API or raw HTTP approaches.
- Adds Node and browser setup requirements.
- More moving parts to debug.

### Prompt-driven synthesis with Groq

Used in:
- All subprojects

What it does:
- Sends a structured analysis prompt to Groq's OpenAI-compatible chat completions API.
- Produces a markdown-style report.

Pros:
- Keeps the output format consistent across workflows.
- Easy to compare prompt strategies between folders.

Cons:
- Final quality depends heavily on prompt design and source quality.
- Larger source payloads can increase token usage and reduce focus.

### Single-file output pattern

Used in:
- All major workflows

What it does:
- Clears prior files in the local `outputs/` folder and writes one main result file.

Pros:
- Keeps outputs easy to find.
- Reduces clutter during repeated experimentation.

Cons:
- Overwrites previous runs unless they were copied elsewhere.
- Not ideal for audit history or experiment tracking.

## Comparison Table

| Workflow | Input Type | Retrieval Method | Depth | Best Use | Main Tradeoff |
| --- | --- | --- | --- | --- | --- |
| `APITest` | News query | NewsAPI | Low-Medium | Broad weekly news scan | Fast, but limited to metadata/snippets |
| `OnlyHeadings` | One URL | Browser scrape | Medium | Quick article structure analysis | Efficient, but misses paragraph detail |
| `WholeArticle` | One URL | Browser scrape | High | Deep single-article analysis | Rich context, but noisier and heavier |
| `AgentCall` | No source input | Prompt only | Variable | Prompt experiments | Easiest, but least grounded |
| `MultiScraper` | Many URLs | Browser scrape | High | Curated weekly synthesis | Strongest context, but most manual/heavy |

## Choosing The Right Process

Use `APITest` when:
- You want broad weekly coverage quickly.
- Source snippets are enough for the first pass.

Use `OnlyHeadings` when:
- You want a fast structural read on one article.
- You want to reduce prompt size while still using real page rendering.

Use `WholeArticle` when:
- One article is important enough to inspect in detail.
- You need nuance from the article body.

Use `AgentCall` when:
- You are testing prompt design or report format.
- You do not need the repo to fetch sources.

Use `MultiScraper` when:
- You already have a shortlist of articles.
- You want the strongest weekly synthesis flow in this repo.

## Main Strengths Of The Repo

- Clear experimentation across multiple retrieval strategies.
- Reusable prompting theme focused on Tata Capital's voice AI use case.
- Good separation between quick scans, single-article analysis, and multi-article synthesis.
- Browser-backed scraping improves coverage for modern sites.

## Main Weaknesses Of The Repo

- The repo is a collection of parallel experiments rather than one unified framework.
- Extraction logic is generic HTML parsing, so publisher-specific cleanup is limited.
- Outputs are overwritten instead of versioned.
- Secret handling is convenient but not production-grade.
- Prompt templates are duplicated across folders, which can make updates harder to keep in sync.

## Recommended Next Improvements

1. Move API keys fully to environment variables or a secret manager.
2. Centralize shared prompt templates and shared Groq helper code.
3. Add dated output filenames or run history to preserve experiments.
4. Add publisher-specific article extraction rules for cleaner full-text scraping.
5. Add a single root entrypoint that lets a user choose between workflow modes.

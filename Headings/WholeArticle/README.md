# WholeArticle

This scraper project collects the full article content, adds it to the same prompt used in `OnlyHeadings`, and saves outputs automatically on every run.

## What it does

1. Fetches the article URL.
2. Extracts:
   - title
   - selected metadata
   - full visible article content blocks
3. Injects that full article content into the provided prompt.
4. Sends the prompt to Groq for contextual analysis.
5. Uses Playwright to load the page in a real browser before extracting content.
6. Saves only the Groq result in `outputs/final_output.md`.

## Setup

Set your Groq API key in the shared root file [api_config.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/api_config.py).

Install the browser helper once:

```bash
npm install
npx playwright install chromium
```

The script already defaults to this article if you do not pass a URL:

`https://venturebeat.com/technology/satya-nadella-warns-that-ai-could-hollow-out-entire-industries-echoing-the-damage-done-by-globalization`

## Usage

Run the scraper and send the result to Groq:

```bash
python3 scraper.py
```

Preview the scraped full article payload:

```bash
python3 scraper.py --scrape-only
```

Save the final prompt to an extra file too:

```bash
python3 scraper.py --save-prompt prompt.txt
```

## Saved Outputs

Every full Groq run replaces the contents of `outputs/` with a single file:

- `final_output.md`
- `--scrape-only` prints the scraped article payload but does not write to `outputs/`.

## Notes

- The Groq prompt text is the same as the `OnlyHeadings` scraper.
- The browser helper requires the local Node dependency install shown above.
- The scraper uses Chromium through Playwright for page loading.

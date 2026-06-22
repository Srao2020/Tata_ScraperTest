# OnlyHeadings

This scraper project collects only the article title, section headings, subheadings, and selected metadata. It does not scrape or summarize the full body text.

## What it does

1. Fetches an article URL.
2. Extracts:
   - title
   - section headings (`h1`, `h2`)
   - subheadings (`h3` to `h6`)
   - selected metadata such as author, description, keywords, publish time, and publisher
3. Injects that reduced article context into the provided prompt.
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

Optional for VS Code:

1. Open the project folder in VS Code.
2. Open the Run and Debug panel.
3. Choose either:
   - `OnlyHeadings: scrape only`
   - `OnlyHeadings: send to Groq`
4. Press Run.

The script already defaults to this article if you do not pass a URL:

`https://venturebeat.com/technology/satya-nadella-warns-that-ai-could-hollow-out-entire-industries-echoing-the-damage-done-by-globalization`

## Usage

Run the scraper and send the result to Groq:

```bash
python3 scraper.py
```

Preview only the extracted article structure:

```bash
python3 scraper.py --scrape-only
```

Save the final prompt before sending it:

```bash
python3 scraper.py --save-prompt prompt.txt
```

Choose a different Groq model:

```bash
python3 scraper.py "https://example.com/article" --model llama3-70b-8192
```

## Notes

- The scraper uses Python's standard library, so no package install is required.
- The browser helper requires the local Node dependency install shown above.
- The scraper uses Chromium through Playwright for page loading.
- The Groq API call uses the OpenAI-compatible chat completions endpoint.
- Every full Groq run replaces the contents of `outputs/` with a single file:
  - `final_output.md`
- `--scrape-only` prints the scraped structure but does not write to `outputs/`.

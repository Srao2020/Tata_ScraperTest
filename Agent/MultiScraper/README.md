# MultiScraper

This scraper project lives under `Agent` and handles multiple article URLs in one run. It scrapes each full article, combines the week's developments into one source pack, sends that combined payload through Groq, and saves one theme-based weekly report.

## Setup

Set your shared Groq key in [api_config.py](/Users/srao/Documents/GitHub/Tata_ScraperTest/api_config.py).

Install the browser helper once:

```bash
cd /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper
npm install
```

## Usage

Paste article URLs into:

- [article_links.txt](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/article_links.txt)

Then run the scraper with no extra arguments:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py
```

Run with multiple URLs directly:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py "https://example.com/article-1" "https://example.com/article-2"
```

Run with a text file of URLs:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py --url-file /path/to/urls.txt
```

Preview the scraped full article payloads without calling Groq:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py --scrape-only "https://example.com/article-1" "https://example.com/article-2"
```

Save the combined weekly prompt:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/scraper.py --save-prompt-dir /tmp/article-prompts --url-file /path/to/urls.txt
```

## Inputs

- `article_links.txt`: default project file with one URL per line
- Positional URLs: one or more article links
- `--url-file`: a plain text file with one URL per line
- If no URLs are provided, the scraper falls back to the existing VentureBeat article example

## Output

The scraper writes one combined file:

- [final_output.md](/Users/srao/Documents/GitHub/Tata_ScraperTest/Agent/MultiScraper/outputs/final_output.md)

Each full run replaces any older file in `outputs/`. The final report groups related developments into broader weekly themes instead of generating one article-by-article summary.

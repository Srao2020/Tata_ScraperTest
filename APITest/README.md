# APITest

This folder contains a small weekly AI news workflow for Tata Capital.

It does three things:

1. Pulls last week's AI-related articles from NewsAPI.
2. Injects those articles into your weekly-update prompt.
3. Sends the prompt to Groq and saves only the final report.

## Setup

The script supports either environment variables or shared values from `api_config.py`.

Required keys:

- `NEWS_API_KEY`
- `GROQ_API_KEY`

Example:

```bash
export NEWS_API_KEY="your_newsapi_key"
export GROQ_API_KEY="your_groq_key"
```

If you prefer shared config, `api_config.py` can expose:

```python
NEWS_API_KEY = "your_newsapi_key"
GROQ_API_KEY = "your_groq_key"
```

## Usage

Run the full workflow:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/news_weekly_update.py
```

Tune the reporting window or query:

```bash
python3 /Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/news_weekly_update.py --days 7 --query '"generative AI" OR LLM OR "voice AI"'
```

## Outputs

The script saves the final report under:

- [outputs](/Users/srao/Documents/GitHub/Tata_ScraperTest/APITest/outputs)

Saved file:

- `weekly_update.md`

## Notes

- NewsAPI `everything` returns article metadata and short content snippets, not full article text.
- The prompt tells Groq to group developments by theme rather than summarize article by article.
- Article data is used in-memory to build the prompt, but only the final Groq output is written to disk.

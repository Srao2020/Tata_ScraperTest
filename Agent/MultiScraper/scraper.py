#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api_config import GROQ_API_KEY


PROMPT_TEMPLATE = """Context
User Profile
Full Name: Puneet Agarwal
Company: Tata Capital
Department: Digital & AI Products
Job Title: Head of AI Product
Profile Summary: AI Product leader at Tata Capital with 11+ years across product management. Currently building voice agentic AI across the customer lifecycle — pre-sales, collections, and retention — in partnership with Sarvam. Passionate about turning frontier AI into compliant, high-impact products for BFSI.
AI Skills:
AI Product Management 
Agentic AI
Voice AI
Conversational AI
Product Strategy
Active Project
AI Voice Agent for Loan Operations
An AI-powered voice agent capable of:
Calling prospective customers
Conducting loan eligibility screening
Answering product questions
Collecting application information
Following up on incomplete applications
Scheduling callbacks with human agents
Supporting collections and payment reminders
Current Status:
{In Progress}
Weekly AI Developments
{WEEKLY_AI_NEWS}

Task
Review all developments and identify the major themes, technological advancements, product launches, research breakthroughs, regulatory changes, and market trends.
Do not summarize articles individually.
Instead, group related developments into broader themes and explain what changed during the week.
For each theme:
Theme
Provide a concise title.
What Happened
Summarize the development across all relevant sources.
Why It Matters
Explain why the development is important in the broader AI landscape.
Potential Relevance to Current Project
Briefly explain how the development could potentially benefit, accelerate, improve, or influence the user's AI Voice Agent project.
Limit this section to 2–4 concise bullets.
Sources
List every source that contributed to the insight.
For each source include:
Article title
Publisher
URL

Final Output Structure
Executive Summary
A concise summary of the most important AI developments this week.
Major AI Developments
Theme 1
What Happened
Why It Matters
Potential Relevance to Current Project
Sources
Theme 2
What Happened
Why It Matters
Potential Relevance to Current Project
Sources
Theme 3
What Happened
Why It Matters
Potential Relevance to Current Project
Sources
(Continue as needed)
What To Watch Next
Identify emerging developments that may become important over the next 30–90 days.
Key Takeaways For The User
Provide 3–5 actionable observations related to the user's current project.
Keep recommendations practical and specific.

Critical Instructions
Group developments by topic, not by article.
Do not produce article-by-article summaries.
Maintain a neutral and factual tone.
Focus on developments from the current reporting period.
Every insight must include links to all supporting source articles.
If multiple articles discuss the same development, combine them into a single theme.
Spend approximately 70% of the output on explaining developments and 30% on project relevance.
Relevance suggestions should be concise and should not dominate the report.
Avoid generic statements such as "AI is growing rapidly" or "this could improve efficiency."
Make direct connections between the development and the user's project where possible.
"""


DEFAULT_ARTICLE_URLS = [
    "https://venturebeat.com/technology/"
    "satya-nadella-warns-that-ai-could-hollow-out-entire-industries-echoing-"
    "the-damage-done-by-globalization"
]

PROJECT_DIR = Path(__file__).resolve().parent
BROWSER_HELPER = PROJECT_DIR / "browser_fetch.js"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
DEFAULT_URL_FILE = PROJECT_DIR / "article_links.txt"


def normalize_space(value: str) -> str:
    # Collapse repeated spacing so saved article text stays readable.
    return " ".join(value.split())


@dataclass
class ArticleData:
    url: str
    final_url: str
    title: str = ""
    publisher: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    content_blocks: List[str] = field(default_factory=list)

    def to_prompt_payload(self) -> str:
        # Build the full article representation that will be inserted into the Groq prompt.
        lines = [
            f"Title: {self.title or 'N/A'}",
            f"Publisher: {self.publisher or 'N/A'}",
            f"URL: {self.final_url}",
            "",
            "Metadata:",
        ]

        if self.metadata:
            for key, value in self.metadata.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- N/A")

        lines.append("")
        lines.append("Article Content:")
        if self.content_blocks:
            lines.extend(self.content_blocks)
        else:
            lines.append("N/A")

        return "\n".join(lines)


class WholeArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.publisher = ""
        self.metadata: Dict[str, str] = {}
        self.content_blocks: List[str] = []
        self._capture_tag: Optional[str] = None
        self._buffer: List[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs):
        # Skip tags that are usually noise for article extraction.
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
            return

        attr_map = {key.lower(): value for key, value in attrs}

        if tag == "title":
            self._capture_tag = "title"
            self._buffer = []
            return

        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"}:
            self._capture_tag = tag
            self._buffer = []

        if tag != "meta":
            return

        # Save metadata that helps with source labeling and article context.
        name = (attr_map.get("name") or attr_map.get("property") or "").strip()
        content = normalize_space(attr_map.get("content", ""))
        if not name or not content:
            return

        lower_name = name.lower()
        if lower_name in {
            "author",
            "description",
            "keywords",
            "article:published_time",
            "article:modified_time",
            "og:site_name",
            "og:type",
            "og:title",
            "twitter:creator",
        }:
            self.metadata[name] = content

        if lower_name == "og:title" and not self.title:
            self.title = content

        if lower_name == "og:site_name" and not self.publisher:
            self.publisher = content

        if lower_name == "application-name" and not self.publisher:
            self.publisher = content

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return

        if self._capture_tag != tag:
            return

        # Convert each captured text block into a clean paragraph-like line.
        text = normalize_space("".join(self._buffer))
        self._capture_tag = None
        self._buffer = []

        if not text:
            return

        if tag == "title":
            self.title = text
            return

        if text not in self.content_blocks:
            self.content_blocks.append(text)

    def handle_data(self, data: str):
        if self._ignored_depth > 0:
            return

        if self._capture_tag:
            self._buffer.append(data)


def fetch_url_with_browser(url: str) -> tuple[str, str]:
    # Load the page through Playwright so tougher sites still render correctly.
    if not BROWSER_HELPER.exists():
        raise RuntimeError(f"Browser helper not found at {BROWSER_HELPER}")

    result = subprocess.run(
        ["node", str(BROWSER_HELPER), url],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "Browser fetch failed."
        raise RuntimeError(stderr)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Browser helper returned invalid JSON.") from exc

    html = payload.get("html", "")
    final_url = payload.get("finalUrl", url)
    if not html:
        raise RuntimeError("Browser helper returned empty HTML.")

    return html, final_url


def scrape_article(url: str) -> ArticleData:
    # Fetch the page with Playwright, then parse out the full visible article text.
    html, final_url = fetch_url_with_browser(url)

    parser = WholeArticleParser()
    parser.feed(html)

    return ArticleData(
        url=url,
        final_url=final_url,
        title=parser.title,
        publisher=parser.publisher,
        metadata=parser.metadata,
        content_blocks=parser.content_blocks,
    )


def build_weekly_news_payload(articles: List[ArticleData]) -> str:
    # Build one combined weekly source pack so Groq can synthesize themes across articles.
    sections: List[str] = []
    for index, article in enumerate(articles, start=1):
        sections.append(f"Source {index}")
        sections.append(article.to_prompt_payload())
        sections.append("")
    return "\n".join(sections).strip()


def build_prompt(articles: List[ArticleData]) -> str:
    # Insert all scraped article payloads into the weekly synthesis prompt.
    weekly_ai_news = build_weekly_news_payload(articles)
    return PROMPT_TEMPLATE.replace("{WEEKLY_AI_NEWS}", weekly_ai_news)


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_final_output(final_output: str) -> Path:
    # Keep the outputs folder simple by storing only one final combined result file.
    OUTPUTS_DIR.mkdir(exist_ok=True)
    for existing_path in OUTPUTS_DIR.iterdir():
        if existing_path.is_file():
            existing_path.unlink()

    final_output_path = OUTPUTS_DIR / "final_output.md"
    write_text_file(final_output_path, final_output)
    return final_output_path


def call_groq(prompt: str, model: str) -> str:
    # Send the prompt to Groq's OpenAI-compatible chat completions endpoint.
    api_key = GROQ_API_KEY.strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise RuntimeError("Set GROQ_API_KEY in api_config.py.")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }

    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TataScraperTest/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace").strip()
        message = f"Groq API error: {exc.code} {exc.reason}"
        if error_body:
            message = f"{message}\n{error_body}"
        raise RuntimeError(message) from exc


def load_urls_from_file(file_path: Path) -> List[str]:
    # Read one URL per line and ignore empty lines or comments.
    urls: List[str] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def collect_urls(args: argparse.Namespace) -> List[str]:
    # Support direct URL arguments, an explicit URL file, or the default project links file.
    urls: List[str] = []

    if args.url_file:
        urls.extend(load_urls_from_file(Path(args.url_file)))
    elif DEFAULT_URL_FILE.exists():
        urls.extend(load_urls_from_file(DEFAULT_URL_FILE))

    urls.extend(args.urls)

    if not urls:
        urls.extend(DEFAULT_ARTICLE_URLS)

    return urls


def format_batch_scrape_output(articles: List[ArticleData]) -> str:
    # Build a readable scrape-only preview for all requested articles.
    sections: List[str] = []
    for index, article in enumerate(articles, start=1):
        sections.append(f"# Article {index}")
        sections.append(article.to_prompt_payload())
        sections.append("")
    return "\n".join(sections).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape multiple full articles and generate one combined weekly report."
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more article URLs to scrape.",
    )
    parser.add_argument(
        "--url-file",
        help="Optional text file with one article URL per line.",
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="Groq model to use. Defaults to llama-3.3-70b-versatile.",
    )
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Print the scraped article payloads without calling Groq.",
    )
    parser.add_argument(
        "--save-prompt-dir",
        help="Optional directory where the combined weekly prompt should be saved.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        urls = collect_urls(args)
        scraped_articles: List[ArticleData] = []
        prompt_dir: Optional[Path] = None
        if args.save_prompt_dir:
            prompt_dir = Path(args.save_prompt_dir)
            prompt_dir.mkdir(parents=True, exist_ok=True)

        for url in urls:
            # Collect every article first so the final prompt can synthesize themes across the week.
            article = scrape_article(url)
            scraped_articles.append(article)

        if args.scrape_only:
            final_output = format_batch_scrape_output(scraped_articles)
            print(final_output)
            return 0

        prompt = build_prompt(scraped_articles)

        if prompt_dir is not None:
            prompt_path = prompt_dir / "weekly_report_prompt.txt"
            write_text_file(prompt_path, prompt)

        final_output = call_groq(prompt, args.model)
        save_final_output(final_output)
        print(final_output)
        return 0
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

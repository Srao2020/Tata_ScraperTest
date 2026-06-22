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
Profile Summary:
AI Product leader at Tata Capital with 11+ years across product management. Currently building voice agentic AI across the customer lifecycle — pre-sales, collections, and retention — in partnership with Sarvam. Passionate about turning frontier AI into compliant, high-impact products for BFSI.
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
Article
{ARTICLE_CONTENT}
Task
Analyze the article and identify the key technological developments, product launches, research breakthroughs, regulatory changes, market implications, and strategic signals.
Do not produce a section-by-section summary of the article.
Instead, identify the most important developments, insights, and implications discussed in the article.
For each development:
Development
Provide a concise title.
What Happened
Summarize the development.
Why It Matters
Explain why the development is important in the broader AI landscape.
Potential Relevance to Current Project
Briefly explain how the development could potentially benefit, accelerate, improve, or influence the user's AI Voice Agent project.
Limit this section to 2–4 concise bullets.
Source
Include:
Article title
Publisher
URL
Final Output Structure
Executive Summary
A concise summary of the most important insights from the article.
Key Developments
Development 1
What Happened
Why It Matters
Potential Relevance to Current Project
Source
(Continue as needed)
Key Takeaways For The User
Provide 3–5 actionable observations related to the user's current project.
Keep recommendations practical and specific.
Critical Instructions
Focus only on information contained in the article.
Do not produce a section-by-section or paragraph-by-paragraph summary.
Maintain a neutral and factual tone.
Explain the significance of the developments, not just what happened.
Every insight must retain a link to the original article.
Spend approximately 70% of the output on explaining developments and 30% on project relevance.
Relevance suggestions should be concise and should not dominate the report.
Avoid generic statements such as "AI is growing rapidly" or "this could improve efficiency."
Make direct connections between the development and the user's project where possible.
"""


DEFAULT_ARTICLE_URL = (
    "https://venturebeat.com/technology/"
    "satya-nadella-warns-that-ai-could-hollow-out-entire-industries-echoing-"
    "the-damage-done-by-globalization"
)

PROJECT_DIR = Path(__file__).resolve().parent
BROWSER_HELPER = PROJECT_DIR / "browser_fetch.js"
OUTPUTS_DIR = PROJECT_DIR / "outputs"


def normalize_space(value: str) -> str:
    # Collapse newlines, tabs, and repeated spaces so headings are easier to read.
    return " ".join(value.split())


@dataclass
class ArticleData:
    url: str
    final_url: str
    title: str = ""
    publisher: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    headings: List[str] = field(default_factory=list)
    subheadings: List[str] = field(default_factory=list)

    def to_prompt_payload(self) -> str:
        # Build the reduced article representation that gets inserted into the Groq prompt.
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
        lines.append("Section Headings:")
        if self.headings:
            for heading in self.headings:
                lines.append(f"- {heading}")
        else:
            lines.append("- N/A")

        lines.append("")
        lines.append("Subheadings:")
        if self.subheadings:
            for subheading in self.subheadings:
                lines.append(f"- {subheading}")
        else:
            lines.append("- N/A")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, object]:
        # Save structured extraction output so each run can be reviewed later.
        return {
            "url": self.url,
            "final_url": self.final_url,
            "title": self.title,
            "publisher": self.publisher,
            "metadata": self.metadata,
            "headings": self.headings,
            "subheadings": self.subheadings,
        }


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.publisher = ""
        self.metadata: Dict[str, str] = {}
        self.headings: List[str] = []
        self.subheadings: List[str] = []
        self._capture_tag: Optional[str] = None
        self._buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        # Keep track of tags whose visible text we want to collect later in handle_data.
        attr_map = {key.lower(): value for key, value in attrs}

        if tag == "title":
            self._capture_tag = "title"
            self._buffer = []
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._capture_tag = tag
            self._buffer = []
            return

        if tag != "meta":
            return

        # Save only metadata that is useful for context and source attribution.
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
        if self._capture_tag != tag:
            return

        # When the tracked tag closes, turn the buffered text into a clean heading value.
        text = normalize_space("".join(self._buffer))
        self._capture_tag = None
        self._buffer = []

        if not text:
            return

        if tag == "title":
            self.title = text
        elif tag in {"h1", "h2"}:
            if text not in self.headings:
                self.headings.append(text)
        elif tag in {"h3", "h4", "h5", "h6"}:
            if text not in self.subheadings:
                self.subheadings.append(text)

    def handle_data(self, data: str):
        if self._capture_tag:
            self._buffer.append(data)


def fetch_url_with_browser(url: str) -> tuple[str, str]:
    # Load the page through Playwright so both scrapers use the same browser-based fetch path.
    if not BROWSER_HELPER.exists():
        raise RuntimeError(f"Browser helper not found at {BROWSER_HELPER}")

    result = subprocess.run(
        ["node", str(BROWSER_HELPER), url],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
        timeout=90,
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
    # Always fetch the page with Playwright so protected sites behave consistently.
    html, final_url = fetch_url_with_browser(url)

    # Parse the rendered page and return only the parts we care about for the prompt.
    parser = ArticleParser()
    parser.feed(html)

    return ArticleData(
        url=url,
        final_url=final_url,
        title=parser.title,
        publisher=parser.publisher,
        metadata=parser.metadata,
        headings=parser.headings,
        subheadings=parser.subheadings,
    )


def build_prompt(article: ArticleData) -> str:
    # Insert the reduced article payload into the exact prompt template the user provided.
    article_content = article.to_prompt_payload()
    return PROMPT_TEMPLATE.replace("{ARTICLE_CONTENT}", article_content)


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_final_output(final_output: str) -> Path:
    # Keep the outputs folder simple by storing only one final result file.
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape only article title, headings, subheadings, and metadata, then send to Groq."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_ARTICLE_URL,
        help="Article URL to scrape. Defaults to the configured VentureBeat example article.",
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="Groq model to use. Defaults to llama-3.3-70b-versatile.",
    )
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Print the reduced article payload without calling Groq.",
    )
    parser.add_argument(
        "--save-prompt",
        help="Optional file path to save the final prompt sent to Groq.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        # Step 1: Collect the reduced article structure.
        article = scrape_article(args.url)
        # Step 2: Turn that structure into the final LLM prompt.
        prompt = build_prompt(article)

        if args.scrape_only:
            # Useful in VS Code when you want to inspect what was captured before using Groq.
            final_output = article.to_prompt_payload()
            if args.save_prompt:
                write_text_file(Path(args.save_prompt), prompt)
            print(final_output)
            return 0

        # Step 3: Send the prompt to Groq and print the contextualized analysis.
        result = call_groq(prompt, args.model)
        save_final_output(result)

        if args.save_prompt:
            write_text_file(Path(args.save_prompt), prompt)
        print(result)
        return 0
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

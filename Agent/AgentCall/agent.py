#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
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

Task
Review all developments and identify the major themes, technological advancements, product launches, research breakthroughs, regulatory changes, and market trends.
Only pull information from these sources from the past week. 
OpenAI News
Google AI & DeepMind Blog
Anthropic News
NVIDIA AI Blog
Reuters AI Coverage
The Batch
TechCrunch AI
Hugging Face Papers

Before using a source/url in the report verify that the url you are using exists and is valid
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


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = PROJECT_DIR / "outputs"


def call_groq(prompt: str, model: str) -> str:
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


def write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_output(final_output: str) -> Path:
    OUTPUTS_DIR.mkdir(exist_ok=True)
    for existing_path in OUTPUTS_DIR.iterdir():
        if existing_path.is_file():
            existing_path.unlink()

    final_output_path = OUTPUTS_DIR / "final_output.md"
    write_text_file(final_output_path, final_output)
    return final_output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send the fixed AgentCall prompt to Groq and save the result."
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="Groq model to use. Defaults to llama-3.3-70b-versatile.",
    )
    parser.add_argument(
        "--save-prompt",
        action="store_true",
        help="Save the exact Groq prompt to the outputs folder.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        final_output = call_groq(PROMPT_TEMPLATE, args.model)
        save_output(final_output)

        if args.save_prompt:
            OUTPUTS_DIR.mkdir(exist_ok=True)
            write_text_file(OUTPUTS_DIR / "prompt.txt", PROMPT_TEMPLATE)

        print(final_output)
        return 0
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

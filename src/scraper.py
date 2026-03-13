import json
import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from src.researcher import load_repo, add_questions

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

# URLs to scrape: list of (url, company_hint) tuples
DEFAULT_URLS = [
    # ("https://igotanoffer.com/blogs/product-manager/microsoft-program-manager-interview#questions", "Microsoft"),
    ("https://www.tryexponent.com/guides/microsoft-pm-interview", "Microsoft"),
    ("https://www.productleadership.com/blog/microsoft-product-manager-interview-questions/", "Microsoft"),
    ("https://www.productmanagementexercises.com/", "Multiple"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

VALID_CATEGORIES = [
    "Product Design",
    "Metrics/Analytical",
    "Strategy",
    "Product Improvement",
    "Behavioral",
    "Estimation",
]


def fetch_page_text(url):
    """Fetches a URL and returns clean plain text."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_questions_with_gemini(page_text, url, company_hint):
    """Uses Gemini to extract PM interview questions from raw page text."""
    if not client:
        print("Warning: GEMINI_API_KEY not set. Cannot extract questions.")
        return []

    prompt = f"""You are a Product Management interview expert.

Extract all distinct Product Manager interview questions from the webpage text below.
Company hint: {company_hint}

Return ONLY a valid JSON array (no markdown, no extra text) where each object has:
- "question": full question text (string)
- "company": company name inferred from context or the hint (string)
- "category": one of exactly these values: {json.dumps(VALID_CATEGORIES)}
- "difficulty": one of "Easy", "Medium", or "Hard"
- "source": "{url}"

If no clear questions are found, return an empty array [].

Webpage text:
{page_text[:30000]}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                print(f"  Error extracting questions from {url}: {e}")
                return []


def deduplicate(new_questions, existing_questions):
    """Filters out questions that are too similar to existing ones."""
    existing_texts = {q["question"].lower().strip() for q in existing_questions}
    unique = []
    for q in new_questions:
        text = q.get("question", "").lower().strip()
        if text and text not in existing_texts:
            unique.append(q)
            existing_texts.add(text)
    return unique


def scrape_and_add_questions(urls_with_hints=None):
    """
    Scrapes PM interview questions from the given URLs and adds new ones to the repo.
    urls_with_hints: list of (url, company_hint) tuples. Defaults to DEFAULT_URLS.
    """
    if urls_with_hints is None:
        urls_with_hints = DEFAULT_URLS

    repo = load_repo()
    all_new = []

    for i, (url, company_hint) in enumerate(urls_with_hints):
        print(f"Scraping: {url}")
        try:
            page_text = fetch_page_text(url)
            questions = extract_questions_with_gemini(page_text, url, company_hint)
            print(f"  Found {len(questions)} questions.")
            all_new.extend(questions)
        except Exception as e:
            print(f"  Failed to scrape {url}: {e}")
        if i < len(urls_with_hints) - 1:
            print("  Waiting 10s before next URL...")
            time.sleep(10)

    unique_new = deduplicate(all_new, repo["questions"])
    print(f"\nTotal new (deduplicated) questions to add: {len(unique_new)}")

    if unique_new:
        add_questions(unique_new)
    else:
        print("No new questions found.")

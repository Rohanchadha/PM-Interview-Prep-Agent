# PM Agent — Project Documentation

## Overview

This project is a **daily PM interview prep agent**. Each run it:

1. Picks a random unsolved PM interview question from a local JSON repository
2. Generates a thorough, framework-based solution using the Gemini AI API
3. Emails the solution to you as formatted HTML with a PDF attachment

The question bank can be populated by scraping real PM interview prep websites (also powered by Gemini).

**Entry point:** `main.py`

**Architecture:**

```
[Scraper] ──scrapes & extracts──► [Researcher / JSON repo]
                                          │
                                     pick_question()
                                          │
                                          ▼
                                      [Solver] ──Gemini──► Markdown solution
                                          │
                                          ▼
                                      [Mailer] ──SMTP──► Your inbox (HTML + PDF)
```

---

## Module: `src/researcher.py`

**Role:** Data layer. Manages the question repository stored at `data/questions_repo.json`.

### Functions

| Function | What it does |
|----------|-------------|
| `load_repo()` | Reads the JSON file; returns `{"questions": [...]}` or an empty dict if the file doesn't exist |
| `save_repo(data)` | Writes a dict back to the JSON file with 2-space indentation |
| `add_questions(new_questions)` | Auto-assigns incrementing integer IDs, sets `solved_on: null` on each question, appends them, and saves |

### Question Schema

Each record in `data/questions_repo.json` looks like:

```json
{
  "id": 1,
  "question": "How would you improve Microsoft Teams?",
  "company": "Microsoft",
  "category": "Product Improvement",
  "difficulty": "Medium",
  "source": "https://...",
  "solved_on": null
}
```

`solved_on` is `null` until the question is answered; then it's set to `"YYYY-MM-DD"`.

Valid categories: `Product Design`, `Metrics/Analytical`, `Strategy`, `Product Improvement`, `Behavioral`, `Estimation`.

---

## Module: `src/scraper.py`

**Role:** Populates the question repo by scraping PM interview websites and using Gemini to extract structured question data.

### Flow

```
fetch_page_text(url)
      │  HTTP GET + BeautifulSoup stripping
      ▼
extract_questions_with_gemini(page_text, url, company_hint)
      │  Gemini prompt → JSON array
      ▼
deduplicate(new_questions, existing_questions)
      │  Lowercase exact-match filter
      ▼
researcher.add_questions(unique_new)
```

### Key Functions

**`fetch_page_text(url)`**
- Makes an HTTP GET request with a browser-like User-Agent header
- Uses `BeautifulSoup` to parse HTML, then removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, and `<aside>` tags
- Returns clean plain text via `get_text(separator="\n", strip=True)`

**`extract_questions_with_gemini(page_text, url, company_hint)`**
- Sends up to 30,000 characters of page text to Gemini
- The prompt instructs Gemini to return **only** a JSON array (no markdown wrapping) where each object has `question`, `company`, `category`, `difficulty`, and `source`
- Includes retry logic: up to 3 attempts with 15s / 30s exponential backoff on HTTP 429 (rate limit) errors
- Strips markdown code fences (` ```json ... ``` `) before calling `json.loads()`
- Returns `[]` on failure

**`deduplicate(new_questions, existing_questions)`**
- Builds a set of lowercase question strings from existing records
- Filters out any new question whose text already exists in that set

**`scrape_and_add_questions()`**
- Iterates `DEFAULT_URLS` (a list of `(url, company_hint)` tuples)
- Waits 10 seconds between pages to avoid rate-limiting
- Calls `add_questions()` with all unique new results

### Gemini Usage in Scraper

- **Model:** `gemini-2.5-flash`
- **Call:** `client.models.generate_content(model="...", contents=prompt)`
- **Prompt goal:** Transform unstructured webpage text into a structured JSON list of PM interview questions
- **Output parsed as:** `json.loads(response.text.strip())`

---

## Module: `src/solver.py`

**Role:** Selects a random unsolved question and generates a complete, framework-based solution using Gemini.

### Key Functions

**`pick_question()`**
- Loads the repo, filters to records where `solved_on` is `null`
- Returns a randomly chosen question dict, or `None` if all questions are solved

**`solve_question(question_obj)`**
- Builds a prompt instructing Gemini to act as a PM interview coach for the specific company
- The framework used in the prompt depends on the question's category:
  - `Product Design` / `Product Improvement` → **CIRCLES framework**
  - `Metrics/Analytical` → **Root Cause Analysis**
  - `Strategy` → **3Cs or Porter's 5 Forces**
- Requests a ≥500 word response in Markdown with company-specific examples
- Returns `response.text` (a Markdown string)
- If `GEMINI_API_KEY` is not set, falls back to hardcoded template skeletons (see below)

**`mark_as_solved(question_id)`**
- Finds the question by ID in the repo and sets `solved_on` to today's date (`YYYY-MM-DD`)
- Saves the updated repo

### Fallback Templates (no API key)

| Template function | Framework |
|-------------------|-----------|
| `solve_design_question_template()` | CIRCLES skeleton |
| `solve_metrics_question_template()` | RCA skeleton |
| `solve_strategy_question_template()` | 3Cs skeleton |
| `solve_generic_question_template()` | Generic outline |

### Gemini Usage in Solver

- **Model:** `gemini-2.5-flash`
- **Call:** `client.models.generate_content(model="...", contents=prompt)`
- **Prompt goal:** Generate a thorough, structured PM interview answer tailored to the company and question type
- **Output:** Markdown string returned directly as the email body

---

## Module: `src/mailer.py`

**Role:** Sends the Markdown solution as a rich HTML email with a PDF attachment via Gmail SMTP.

### Flow inside `send_email()`

1. **Build message headers** — `From`, `To`, `Subject` on a `MIMEMultipart('mixed')` container
2. **Convert Markdown → HTML** using the `markdown` library with `extra` and `nl2br` extensions
3. **Attach email body** as both `text/plain` (raw Markdown) and `text/html` (rendered HTML) inside a `MIMEMultipart('alternative')` part
4. **Generate PDF** (requires `fpdf2`):
   - Iterates each line of the Markdown body
   - Detects heading levels (`# `, `## `, `### `) and applies bold + scaled font sizes (16pt / 14pt / 12pt)
   - Strips inline Markdown (`*`, `_`, `` ` ``) with regex before rendering
   - Sanitizes Unicode via `_ascii_safe()`: replaces em-dashes, curly quotes, bullet points, etc. with ASCII equivalents, then encodes to latin-1
   - Outputs PDF bytes and attaches as `application/pdf` named `solution.pdf`
   - If `fpdf2` is not installed, the PDF step is skipped with a warning
5. **Send via SMTP:**
   - Opens `smtplib.SMTP(smtp_server, smtp_port)` (default: `smtp.gmail.com:587`)
   - Upgrades connection to TLS using `starttls()`
   - Authenticates with `smtp_username` / `smtp_password`
   - Sends the message and quits

---

## Gemini API — End-to-End Summary

The project uses Google's `google-genai` Python SDK (`from google import genai`).

### Client Initialization (both `scraper.py` and `solver.py`)

```python
from google import genai
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
```

The API key is loaded from the `.env` file via `python-dotenv` (called in `main.py`).

### Usage Summary

| Module | Model | Purpose | Input → Output |
|--------|-------|---------|----------------|
| `scraper.py` | `gemini-2.5-flash` | Extract structured PM questions from raw webpage text | 30k chars of HTML text → JSON array of question objects |
| `solver.py` | `gemini-2.5-flash` | Generate a framework-based PM interview answer | Question + company + category → Markdown solution |

### Calling Pattern

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,   # plain string
)
result = response.text  # plain string back
```

No streaming is used. Both calls are synchronous.

---

## How to Trigger an Email

### Step 1 — Check Your `.env`

The `.env` file in the `pm_agent/` directory must contain:

```env
GEMINI_API_KEY=your-gemini-api-key
USER_EMAIL=recipient@example.com
SMTP_USERNAME=sender@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

> **Gmail App Password required.** Gmail blocks regular passwords for SMTP. Generate an App Password at:
> `myaccount.google.com → Security → 2-Step Verification → App Passwords`
> Select "Mail" and your device; it generates a 16-character password.

### Step 2 — Install Dependencies

```bash
cd pm_agent
pip install -r requirements.txt
pip install fpdf2          # for PDF attachment (not in requirements.txt)
```

### Step 3 — Populate the Question Bank (first time only)

If `data/questions_repo.json` is empty or missing:

```bash
python main.py --scrape
```

This scrapes the configured URLs, calls Gemini to extract questions, deduplicates, and saves them to the JSON repo.

### Step 4 — Send the Email

**Dry run** (no email sent — prints a preview to terminal):

```bash
python main.py
```

**Live run** (actually sends the email):

```bash
python main.py --live
```

On a live run, `main.py`:
1. Calls `pick_question()` — picks a random unsolved question
2. Calls `solve_question()` — generates the Gemini solution
3. Calls `send_email()` — sends HTML + PDF to `USER_EMAIL`
4. Calls `mark_as_solved()` — stamps the question with today's date so it won't repeat

### Automating Daily Emails (macOS)

To run this every morning automatically, add a cron job:

```bash
crontab -e
```

```
0 8 * * * cd /path/to/pm_agent && /usr/bin/python3 main.py --live >> /tmp/pm_agent.log 2>&1
```

This runs at 8:00 AM every day.

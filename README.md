# PM Interview Prep Agent

A daily PM interview prep agent that scrapes real interview questions, generates framework-based solutions using Gemini AI, and emails them to you every morning as formatted HTML with a PDF attachment.

## How It Works

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

1. Searches the web for PM interview question pages (via DuckDuckGo) or accepts URLs directly
2. Scrapes those pages and uses Gemini to extract structured questions into a local JSON repo
3. Picks a random unsolved question from the repo
4. Generates a thorough, framework-based solution (CIRCLES, RCA, 3Cs, Porter's 5 Forces) using Gemini
5. Emails the solution as rich HTML + PDF to your inbox

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install fpdf2   # for PDF attachment
```

### 2. Configure `.env`

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your-gemini-api-key
USER_EMAIL=recipient@example.com
SMTP_USERNAME=sender@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

> **Gmail App Password required.** Go to `myaccount.google.com → Security → 2-Step Verification → App Passwords` and generate a 16-character password for "Mail".

### 3. Populate the Question Bank (first time only)

Search the web by company name — the agent automatically finds and scrapes relevant pages:
```bash
python main.py --scrape --company "Google"
python main.py --scrape --company "Meta"
```

Or provide URLs directly:
```bash
python main.py --scrape --urls "https://example.com/google-pm-questions,https://example2.com"
```

Or combine both (searched URLs + explicit URLs):
```bash
python main.py --scrape --company "Google" --urls "https://specific-page.com"
```

Or fall back to the built-in default URLs:
```bash
python main.py --scrape
```

## Usage

**Dry run** — generates a solution and prints a preview (no email sent):
```bash
python main.py
```

**Live run** — generates a solution and sends it to your inbox:
```bash
python main.py --live
```

## Automate Daily Emails (GitHub Actions)

The repo includes a GitHub Actions workflow (`.github/workflows/daily_pm_agent.yml`) that runs `python main.py --live` at 8:00 AM UTC every day and commits the updated `questions_repo.json` back to the repo to persist state between runs.

**Setup:**

1. Push the project to a GitHub repo
2. Add these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `USER_EMAIL` | Your email address |
| `SMTP_USERNAME` | Gmail sender address |
| `SMTP_PASSWORD` | Gmail App Password (16 chars) |

3. The workflow fires automatically every day. To test it manually, go to **Actions → Daily PM Agent → Run workflow**.

## Project Structure

```
pm_agent/
├── main.py                          # Entry point (CLI flags: --scrape, --company, --urls, --live)
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily_pm_agent.yml       # GitHub Actions cron workflow
├── data/
│   └── questions_repo.json          # Local question bank
└── src/
    ├── researcher.py                # JSON repo read/write layer
    ├── scraper.py                   # Web search (DuckDuckGo) + scraping + Gemini extraction
    ├── solver.py                    # Question selection + Gemini solution generation
    └── mailer.py                    # HTML + PDF email via Gmail SMTP
```

## Question Schema

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

Categories: `Product Design`, `Metrics/Analytical`, `Strategy`, `Product Improvement`, `Behavioral`, `Estimation`

## Tech Stack

- **AI:** Google Gemini 2.5 Flash (`google-genai`)
- **Web Search:** DuckDuckGo (`duckduckgo-search`) — no API key required
- **Email:** Gmail SMTP (`smtplib`)
- **PDF:** `fpdf2`
- **Scraping:** `requests` + `BeautifulSoup`
- **Config:** `python-dotenv`
- **Automation:** GitHub Actions (`.github/workflows/daily_pm_agent.yml`)

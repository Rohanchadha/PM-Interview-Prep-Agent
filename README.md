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

1. Scrapes PM interview prep websites using Gemini to extract structured questions
2. Picks a random unsolved question from the local JSON repository
3. Generates a thorough, framework-based solution (CIRCLES, RCA, 3Cs, Porter's 5 Forces) using Gemini
4. Emails the solution as rich HTML + PDF to your inbox

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

## Automate Daily Emails (macOS)

```bash
crontab -e
```

```
0 8 * * * cd /path/to/pm_agent && /usr/bin/python3 main.py --live >> /tmp/pm_agent.log 2>&1
```

Runs at 8:00 AM every day.

## Project Structure

```
pm_agent/
├── main.py                  # Entry point
├── requirements.txt
├── data/
│   └── questions_repo.json  # Local question bank
└── src/
    ├── researcher.py        # JSON repo read/write layer
    ├── scraper.py           # Web scraping + Gemini extraction
    ├── solver.py            # Question selection + Gemini solution generation
    └── mailer.py            # HTML + PDF email via Gmail SMTP
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
- **Email:** Gmail SMTP (`smtplib`)
- **PDF:** `fpdf2`
- **Scraping:** `requests` + `BeautifulSoup`
- **Config:** `python-dotenv`

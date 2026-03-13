import os
import sys
from dotenv import load_dotenv
load_dotenv()

from src.solver import pick_question, solve_question, mark_as_solved
from src.mailer import send_email
from src.scraper import scrape_and_add_questions

# Configuration (Use environment variables for security)
USER_EMAIL = os.environ.get("USER_EMAIL", "recipient@example.com")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "sender@example.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your-app-password")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def run_daily_agent(dry_run=True):
    print("--- PM Interview Agent Started ---")
    
    # 1. Pick a question
    question = pick_question()
    if not question:
        print("No unsolved questions in the repository.")
        return

    print(f"Selected Question: {question['question']} ({question['company']})")

    # 2. Solve the question
    solution_md = solve_question(question)
    print("Solution generated.")

    # 3. Send email
    subject = f"Daily PM Question: {question['company']} - {question['category']}"
    
    if dry_run:
        print("\n[DRY RUN] Email would be sent to:", USER_EMAIL)
        print("Subject:", subject)
        print("Content Preview:\n", solution_md[:200], "...")
    else:
        success = send_email(
            subject=subject,
            body=solution_md,
            to_email=USER_EMAIL,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            smtp_username=SMTP_USERNAME,
            smtp_password=SMTP_PASSWORD
        )
        if success:
            mark_as_solved(question['id'])

    print("--- PM Interview Agent Completed ---")

if __name__ == "__main__":
    if "--scrape" in sys.argv:
        scrape_and_add_questions()
    else:
        # Default to dry run unless --live flag is passed
        is_live = "--live" in sys.argv
        run_daily_agent(dry_run=not is_live)

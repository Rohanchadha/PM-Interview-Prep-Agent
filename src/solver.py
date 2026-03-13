import json
import os
import random
from google import genai

REPO_PATH = os.path.join(os.path.dirname(__file__), "../data/questions_repo.json")

# Configuration - Use environment variable for API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None

def pick_question():
    if not os.path.exists(REPO_PATH):
        return None
    with open(REPO_PATH, "r") as f:
        repo = json.load(f)
    
    unsolved = [q for q in repo["questions"] if q["solved_on"] is None]
    if not unsolved:
        return None
    return random.choice(unsolved)

from datetime import datetime

def solve_question(question_obj):
    """
    Generates a thorough PM solution based on the category of the question.
    Uses Gemini if API key is present, otherwise falls back to templates.
    """
    q_text = question_obj["question"]
    company = question_obj["company"]
    category = question_obj["category"].lower()
    
    if not client:
        print("Warning: GEMINI_API_KEY not found. Falling back to template-based solution.")
        if "design" in category or "improvement" in category:
            return solve_design_question_template(q_text, company)
        elif "metrics" in category or "analytical" in category:
            return solve_metrics_question_template(q_text, company)
        elif "strategy" in category:
            return solve_strategy_question_template(q_text, company)
        else:
            return solve_generic_question_template(q_text, company)

    # Use LLM with specific frameworks
    prompt = f"""
    You are an expert Product Manager interview coach. 
    Solve the following interview question for {company} thoroughly.
    
    Question: {q_text}
    Category: {category}
    
    Guidelines:
    - If it's a Design/Improvement question, use the CIRCLES framework.
    - If it's a Metrics/Execution question, use Root Cause Analysis.
    - If it's a Strategy question, use 3Cs or Porter's 5 Forces.
    - Provide a structured, professional, and insightful response in Markdown.
    - Include specific examples relevant to {company}.
    - Ensure the solution is thorough (at least 500 words).
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return solve_generic_question_template(q_text, company)

def solve_design_question_template(q, company):
    return f"""
# [TEMPLATE] PM Interview Solution: {q}
**Company:** {company} | **Category:** Product Design (Framework: CIRCLES)

## 1. Comprehend Situation
- **Goal:** Increase engagement or revenue.
- **Constraints:** Limited budget and time.

## 2. Identify User Segments
- Primary: Regular users.
- Secondary: Power users.

## 3. Report Customer Needs
- Pain Point 1: Difficulty in navigation.
- Pain Point 2: Lack of personalization.

## 4. Prioritization
- Focus on Pain Point 1 for maximum impact.

## 5. List Solutions
- Solution A: Redesign the UI.
- Solution B: Add AI-driven recommendations.

## 6. Evaluation
- UI redesign is high cost but essential.

## 7. Recommendation
- Start with a phased UI rollout.
"""

def solve_metrics_question_template(q, company):
    return f"""
# [TEMPLATE] PM Interview Solution: {q}
**Company:** {company} | **Category:** Metrics & Execution (Framework: RCA)

## 1. Clarification
- Sudden drop or gradual? Local or global?

## 2. External Factors
- Competitor activity, seasonal shifts.

## 3. Internal Factors
- Recent code changes, server health.

## 4. Hypothesis
- A bug in the latest release is causing churn.

## 5. Action
- Verify hypothesis with data and fix bugs.
"""

def solve_strategy_question_template(q, company):
    return f"""
# [TEMPLATE] PM Interview Solution: {q}
**Company:** {company} | **Category:** Strategy (Framework: 3Cs)

## 1. Company
- Core strengths and vision.

## 2. Competition
- Market landscape and rivals.

## 3. Customers
- Evolving needs and segments.

## 4. Recommendation
- Focus on building a moat through proprietary tech.
"""

def solve_generic_question_template(q, company):
    return f"""
# [TEMPLATE] PM Interview Solution: {q}
**Company:** {company}

## 1. Approach
Thorough analysis of the problem statement.

## 2. Key Insights
Actionable takeaways.

## 3. Conclusion
Final strategic advice.
"""

def mark_as_solved(question_id):
    with open(REPO_PATH, "r") as f:
        repo = json.load(f)
    
    for q in repo["questions"]:
        if q["id"] == question_id:
            q["solved_on"] = datetime.now().strftime("%Y-%m-%d")
            break
            
    with open(REPO_PATH, "w") as f:
        json.dump(repo, f, indent=2)

import json
import os

REPO_PATH = os.path.join(os.path.dirname(__file__), "../data/questions_repo.json")

def load_repo():
    if not os.path.exists(REPO_PATH):
        return {"questions": []}
    with open(REPO_PATH, "r") as f:
        return json.load(f)

def save_repo(data):
    with open(REPO_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_questions(new_questions):
    """
    new_questions: list of dicts with question, company, category, difficulty, source
    """
    repo = load_repo()
    current_ids = [q["id"] for q in repo["questions"]]
    next_id = max(current_ids) + 1 if current_ids else 1
    
    for q in new_questions:
        q["id"] = next_id
        q["solved_on"] = None
        repo["questions"].append(q)
        next_id += 1
    
    save_repo(repo)
    print(f"Added {len(new_questions)} new questions to repository.")

if __name__ == "__main__":
    # Placeholder for daily research logic
    # In a real scenario, this might call an LLM to generate/search for new variants
    print("Researcher script ready.")

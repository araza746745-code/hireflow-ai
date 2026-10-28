from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define the information shared by our nodes
class HiringState(TypedDict):
    job_title: str
    required_skills: list[str]
    resume_text: str
    candidate_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    review_summary: str


# 2. Node: Find job-related skills in the resume
def extract_skills(state: HiringState):
    resume = state["resume_text"].lower()

    # Look for each required skill in the resume
    skills = [
        skill
        for skill in state["required_skills"]
        if skill.lower() in resume
    ]

    return {"candidate_skills": skills}


# 3. Node: Compare the skills with the job requirements
def match_skills(state: HiringState):
    required = state["required_skills"]
    found = state["candidate_skills"]

    matched = [skill for skill in required if skill in found]
    missing = [skill for skill in required if skill not in found]

    return {
        "matched_skills": matched,
        "missing_skills": missing
    }


# 4. Node: Prepare a summary for HR
def prepare_review(state: HiringState):
    summary = (
        f"Job: {state['job_title']}\n"
        f"Skills found: {', '.join(state['matched_skills']) or 'None'}\n"
        f"Skills not found: {', '.join(state['missing_skills']) or 'None'}\n"
        "Next action: Human HR review required."
    )

    return {"review_summary": summary}


# 5. Create the graph
builder = StateGraph(HiringState)

builder.add_node("extract_skills", extract_skills)
builder.add_node("match_skills", match_skills)
builder.add_node("prepare_review", prepare_review)

# 6. Connect the nodes
builder.add_edge(START, "extract_skills")
builder.add_edge("extract_skills", "match_skills")
builder.add_edge("match_skills", "prepare_review")
builder.add_edge("prepare_review", END)

# 7. Compile the graph
hiring_graph = builder.compile()
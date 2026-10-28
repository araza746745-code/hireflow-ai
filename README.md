HireFlow AI — AI-Powered Recruitment Platform

HireFlow AI is a recruitment workflow web application built to simplify job creation, resume screening, skill matching, and candidate review.

🚀 Live Demo

https://hireflow-ai-w3a3.onrender.com

✨ Features

- Create job descriptions with required skills
- Upload candidate resumes in PDF format
- Extract resume text using PyMuPDF
- Match resume skills against job requirements
- Store job and application records using SQLite
- Support human HR review before interview decisions
- Approve or decline candidate applications

🛠️ Tech Stack

- Python
- FastAPI
- LangGraph
- SQLite
- PyMuPDF
- HTML and CSS
- Jinja2
- Git and GitHub
- Render

⚙️ Run Locally

1. Clone the repository:
   
   "git clone https://github.com/araza746745-code/hireflow-ai.git"

2. Open the project directory:
   
   "cd hireflow-ai"

3. Create and activate a virtual environment:
   
   "python -m venv .venv"
   
   Windows PowerShell:
   
   ".venv\Scripts\Activate.ps1"

4. Install dependencies:
   
   "pip install -r requirements.txt"

5. Start the application:
   
   "python -m uvicorn app.main:app --reload"

6. Open this URL in your browser:
   
   "http://127.0.0.1:8000"

🔄 Workflow

1. HR creates a job description.
2. A candidate submits their details and PDF resume.
3. The application extracts text and checks for required skills.
4. HR reviews the results and decides whether to proceed with an interview.

⚠️ Project Notes

This is a portfolio and learning project. Skill matching currently uses basic keyword matching, not a fully trained AI model. Human review is required before making recruitment decisions.

Before using real candidate data, implement authentication, access controls, secure data handling, and appropriate database persistence.

👨‍💻 Author

MD Ahmad Raza

GitHub: https://github.com/araza746745-code
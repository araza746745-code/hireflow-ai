from pathlib import Path
from uuid import uuid4
import sqlite3
import json

from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.resume_parser import extract_resume_text
from app.workflow import hiring_graph


# Find project folders
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Database file will be created automatically
DB_PATH = PROJECT_DIR / "hiring.db"


# Connect to SQLite database
def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Create tables if they do not exist
def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                skills TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                job_id TEXT NOT NULL,
                matched_skills TEXT NOT NULL,
                missing_skills TEXT NOT NULL,
                review_summary TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)


# Prepare database before serving requests
initialize_database()

app = FastAPI(title="AI Hiring Agent")

# Connect CSS folder
app.mount(
    "/static",
    StaticFiles(directory=PROJECT_DIR / "static"),
    name="static"
)

# Connect HTML templates folder
templates = Jinja2Templates(
    directory=PROJECT_DIR / "templates"
)


# Read all jobs from database
def get_jobs():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM jobs ORDER BY rowid DESC"
        ).fetchall()

    result = []

    for row in rows:
        job = dict(row)
        job["skills"] = json.loads(job["skills"])
        result.append(job)

    return result


# Read all applications from database
def get_applications():
    query = """
        SELECT
            applications.*,
            jobs.title AS job_title
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        ORDER BY applications.rowid DESC
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    result = []

    for row in rows:
        candidate = dict(row)
        candidate["matched_skills"] = json.loads(
            candidate["matched_skills"]
        )
        candidate["missing_skills"] = json.loads(
            candidate["missing_skills"]
        )
        result.append(candidate)

    return result


# Show dashboard
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "jobs": get_jobs(),
            "applications": get_applications()
        }
    )


# Create and save a job
@app.post("/jobs")
def create_job(
    title: str = Form(...),
    description: str = Form(...),
    skills: str = Form(...)
):
    job_id = str(uuid4())

    skill_list = [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]

    with get_db() as db:
        db.execute(
            """
            INSERT INTO jobs (id, title, description, skills)
            VALUES (?, ?, ?, ?)
            """,
            (
                job_id,
                title.strip(),
                description.strip(),
                json.dumps(skill_list)
            )
        )

    return RedirectResponse("/", status_code=303)


# Receive candidate application and PDF resume
@app.post("/apply")
async def apply(
    name: str = Form(...),
    email: str = Form(...),
    job_id: str = Form(...),
    resume: UploadFile = File(...)
):
    # Find the selected job
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(404, "Job not found")

    # Basic PDF validation
    if (
        resume.content_type != "application/pdf"
        or not resume.filename.lower().endswith(".pdf")
    ):
        raise HTTPException(400, "Please upload a PDF")

    pdf_bytes = await resume.read(5 * 1024 * 1024 + 1)

    if len(pdf_bytes) > 5 * 1024 * 1024:
        raise HTTPException(413, "PDF must be under 5 MB")

    # Check the actual PDF file signature
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(400, "Invalid PDF file")

    try:
        resume_text = extract_resume_text(pdf_bytes)
    except Exception:
        raise HTTPException(400, "Could not read PDF text")

    if not resume_text.strip():
        raise HTTPException(
            400,
            "No readable text found. Try a text-based PDF."
        )

    job = dict(row)
    required_skills = json.loads(job["skills"])

    # Run the existing LangGraph workflow
    result = hiring_graph.invoke({
        "job_title": job["title"],
        "required_skills": required_skills,
        "resume_text": resume_text,
        "candidate_skills": [],
        "matched_skills": [],
        "missing_skills": [],
        "review_summary": ""
    })

    application_id = str(uuid4())

    # Save application permanently
    with get_db() as db:
        db.execute(
            """
            INSERT INTO applications (
                id, name, email, job_id,
                matched_skills, missing_skills,
                review_summary, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                application_id,
                name.strip(),
                email.strip(),
                job_id,
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]),
                result["review_summary"],
                "Pending HR Review"
            )
        )

    return RedirectResponse("/", status_code=303)


# HR approves interview stage
@app.post("/applications/{application_id}/approve")
def approve_interview(application_id: str):
    with get_db() as db:
        cursor = db.execute(
            """
            UPDATE applications
            SET status = ?
            WHERE id = ? AND status = ?
            """,
            (
                "Interview Approved",
                application_id,
                "Pending HR Review"
            )
        )

        if cursor.rowcount == 0:
            exists = db.execute(
                "SELECT id FROM applications WHERE id = ?",
                (application_id,)
            ).fetchone()

            if exists is None:
                raise HTTPException(404, "Application not found")

            raise HTTPException(400, "Application already reviewed")

    return RedirectResponse("/", status_code=303)


# HR marks application as not proceeding
@app.post("/applications/{application_id}/decline")
def decline_application(application_id: str):
    with get_db() as db:
        cursor = db.execute(
            """
            UPDATE applications
            SET status = ?
            WHERE id = ? AND status = ?
            """,
            (
                "Not Proceeding",
                application_id,
                "Pending HR Review"
            )
        )

        if cursor.rowcount == 0:
            exists = db.execute(
                "SELECT id FROM applications WHERE id = ?",
                (application_id,)
            ).fetchone()

            if exists is None:
                raise HTTPException(404, "Application not found")

            raise HTTPException(400, "Application already reviewed")

    return RedirectResponse("/", status_code=303)
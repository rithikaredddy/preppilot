from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from sqlalchemy import func, select

from app.extensions import db
from app.models import ResumeAnalysis
from app.services.llm import parse_json_object
from app.services.resume_service import ats_score, required_skills, skill_present
from tests.test_auth import auth_header, register_tpo, student_payload

RICH_LINES = [
    "Ada Lovelace",
    "ada@example.com",
    "9876543210",
    "Education",
    "B.Tech Computer Science and Engineering",
    "Skills",
    "Python, SQL, and Java",
    "Projects",
    "- Built a placement portal for campus drives",
    "- Wrote SQL reports for student outcomes",
    "- Designed an API for interview scheduling",
    "Experience",
    "Intern at the campus computing lab",
]
SPARSE_LINES = [
    "This short resume has enough characters to extract but none of the usual sections.",
]
ANALYSIS = {
    "skills": ["Python", "SQL", "Java"],
    "education": ["B.Tech Computer Science and Engineering"],
    "projects": ["Placement portal"],
    "experience": ["Campus computing lab intern"],
    "certifications": [],
    "required_skills": ["Python", "Kubernetes"],
    "formatting_issues": [],
    "suggestions": [
        "Add a project that uses Kubernetes.",
        "Quantify how many students used the portal.",
        "Keep contact details in the page header.",
    ],
}


@pytest.fixture(autouse=True)
def clear_llm(app):
    app.extensions.pop("llm", None)
    yield
    app.extensions.pop("llm", None)


def scripted(app, responses):
    queue = list(responses)

    def _call(_instructions, payload):
        assert isinstance(payload, dict)
        if not queue:
            raise AssertionError("The workflow called the model more times than the test supplied.")
        return queue.pop(0)

    app.extensions["llm"] = _call
    return queue


def register(client, **overrides):
    response = client.post("/api/v1/auth/register", json=student_payload(**overrides))
    assert response.status_code == 201
    return response.get_json()["access_token"]


def docx_bytes(lines):
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def pdf_bytes():
    buffer = BytesIO()
    drawing = canvas.Canvas(buffer)
    drawing.drawString(72, 720, "Ada Lovelace ada@example.com 9876543210 Education")
    drawing.drawString(72, 700, "Skills Python SQL Projects Experience built a placement portal")
    drawing.save()
    return buffer.getvalue()


def upload(client, token, content, filename):
    return client.post(
        "/api/v1/resumes",
        data={"file": (BytesIO(content), filename)},
        headers=auth_header(token),
        content_type="multipart/form-data",
    )


def test_parse_fenced_json():
    parsed = parse_json_object('```json\n{"question": "Why this role?"}\n```')
    assert parsed["question"] == "Why this role?"


def test_ats_score_depends_on_the_document():
    rich = ats_score("\n".join(RICH_LINES), [])
    sparse = ats_score("\n".join(SPARSE_LINES), [])
    penalized = ats_score("\n".join(RICH_LINES), ["Missing dates", "Dense paragraph"])
    assert rich > sparse
    assert penalized < rich
    assert required_skills("", ["Leadership"])[0] == "Python"
    assert skill_present("Python", ["Python programming"], "no mention")
    assert not skill_present("Kubernetes", ["Python"], "built APIs")


def test_resume_analysis_stores_computed_scores(client, app):
    token = register(client)
    uploaded = upload(client, token, docx_bytes(RICH_LINES), "ada.docx")
    assert uploaded.status_code == 201
    resume_id = uploaded.get_json()["id"]
    preview = client.get(f"/api/v1/resumes/{resume_id}", headers=auth_header(token))
    assert "Python" in preview.get_json()["extracted_preview"]

    scripted(app, [ANALYSIS])
    analyzed = client.post(
        f"/api/v1/resumes/{resume_id}/analyze",
        json={
            "target_role": "Data analyst",
            "job_description": "We need Python and Kubernetes for this analyst role.",
        },
        headers=auth_header(token),
    )
    assert analyzed.status_code == 201
    body = analyzed.get_json()
    assert body["skill_match_percentage"] == 50.0
    assert body["missing_skills"] == ["Kubernetes"]
    assert body["ats_score"] == ats_score("\n".join(RICH_LINES), [])
    assert "ats_score" not in ANALYSIS

    report = client.get(f"/api/v1/resume-analyses/{body['id']}/report", headers=auth_header(token))
    assert report.status_code == 200
    assert report.data.startswith(b"%PDF")
    report_text = "\n".join(
        page.extract_text() or "" for page in PdfReader(BytesIO(report.data)).pages
    )
    assert "Kubernetes" in report_text
    assert "Data analyst" in report_text

    summary = client.get("/api/v1/dashboard/summary", headers=auth_header(token))
    assert summary.get_json()["resume_score"] == body["ats_score"]
    assert summary.get_json()["completed_sessions"] == 0


def test_sparse_resume_scores_lower_than_a_structured_one(client, app):
    token = register(client, email="sparse@example.com", roll_number="CS010")
    scripted(app, [ANALYSIS, {**ANALYSIS, "formatting_issues": []}])
    rich = upload(client, token, docx_bytes(RICH_LINES), "rich.docx")
    sparse = upload(client, token, docx_bytes(SPARSE_LINES), "sparse.docx")
    rich_score = client.post(
        f"/api/v1/resumes/{rich.get_json()['id']}/analyze",
        json={"target_role": "Analyst", "job_description": "Python and Kubernetes"},
        headers=auth_header(token),
    ).get_json()["ats_score"]
    sparse_score = client.post(
        f"/api/v1/resumes/{sparse.get_json()['id']}/analyze",
        json={"target_role": "Analyst", "job_description": "Python and Kubernetes"},
        headers=auth_header(token),
    ).get_json()["ats_score"]
    assert rich_score > sparse_score


def test_pdf_extraction_and_rejected_files(client, app):
    token = register(client, email="files@example.com", roll_number="CS011")
    pdf = upload(client, token, pdf_bytes(), "ada.pdf")
    assert pdf.status_code == 201
    assert (
        "Ada Lovelace"
        in client.get(
            f"/api/v1/resumes/{pdf.get_json()['id']}", headers=auth_header(token)
        ).get_json()["extracted_preview"]
    )
    text = upload(client, token, b"not a resume", "notes.txt")
    assert text.status_code == 415
    original_limit = app.config["MAX_UPLOAD_BYTES"]
    app.config["MAX_UPLOAD_BYTES"] = 30
    try:
        oversized = upload(client, token, docx_bytes(RICH_LINES), "big.docx")
        assert oversized.status_code == 413
    finally:
        app.config["MAX_UPLOAD_BYTES"] = original_limit


def test_missing_model_key_does_not_invent_an_analysis(client, app):
    token = register(client, email="nokey@example.com", roll_number="CS012")
    uploaded = upload(client, token, docx_bytes(RICH_LINES), "ada.docx")
    response = client.post(
        f"/api/v1/resumes/{uploaded.get_json()['id']}/analyze",
        json={"target_role": "Data analyst", "job_description": "Python"},
        headers=auth_header(token),
    )
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "llm_not_configured"
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(ResumeAnalysis)) == 0


def test_hr_interview_stores_scores_from_turn_evaluations(client, app):
    token = register(client, email="hr@example.com", roll_number="CS013")
    first = {
        "scores": {
            "language_specificity": 80,
            "communication": 70,
            "relevance": 40,
            "professionalism": 90,
        },
        "feedback": "The tone is professional, but the example does not name your action.",
        "next_question": "What did you do when your teammate missed the deadline?",
        "is_follow_up": True,
    }
    second = {
        "scores": {
            "language_specificity": 60,
            "communication": 80,
            "relevance": 50,
            "professionalism": 70,
        },
        "feedback": "You named the deadline, and the action is still too general.",
        "next_question": None,
        "is_follow_up": False,
    }
    summary = {
        "overall_score": 10,
        "strengths": ["Professional tone"],
        "improvements": ["Name the action you took"],
        "weak_areas": ["Give a concrete example"],
    }
    scripted(
        app,
        [
            {"question": "Tell me about a time you worked on a team.", "is_follow_up": False},
            first,
            second,
            summary,
        ],
    )
    started = client.post("/api/v1/interviews", json={"kind": "hr"}, headers=auth_header(token))
    assert started.status_code == 201
    session_id = started.get_json()["id"]
    assert started.get_json()["turns"][0]["question_text"].startswith("Tell me")

    too_soon = client.post(f"/api/v1/interviews/{session_id}/complete", headers=auth_header(token))
    assert too_soon.status_code == 400

    answer_one = client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"answer": "I worked with a teammate on a class project."},
        headers=auth_header(token),
    )
    assert answer_one.status_code == 200
    assert answer_one.get_json()["turns"][1]["is_follow_up"] is True
    answer_two = client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"answer": "I sent a reminder before the deadline."},
        headers=auth_header(token),
    )
    assert answer_two.status_code == 200

    finished = client.post(f"/api/v1/interviews/{session_id}/complete", headers=auth_header(token))
    assert finished.status_code == 200
    body = finished.get_json()
    flat = [*first["scores"].values(), *second["scores"].values()]
    expected = round(sum(flat) / len(flat), 2)
    assert body["overall_score"] == expected
    assert body["overall_score"] != 10
    assert "Relevance" in body["weak_areas"]
    assert body["status"] == "completed"

    stored = client.get(f"/api/v1/interviews/{session_id}", headers=auth_header(token))
    assert stored.get_json()["turns"][0]["answer_text"].startswith("I worked")
    dashboard = client.get("/api/v1/dashboard/summary", headers=auth_header(token))
    assert dashboard.get_json()["hr_score"] == expected
    assert dashboard.get_json()["completed_sessions"] == 1


def test_technical_interview_tracks_topic_and_weak_area(client, app):
    token = register(client, email="tech@example.com", roll_number="CS014")
    scores = {"correctness": 40, "depth": 30, "clarity": 80, "relevance": 70}
    scripted(
        app,
        [
            {"question": "What is a primary key?", "is_follow_up": False},
            {
                "scores": scores,
                "feedback": "The definition is incomplete.",
                "next_question": "How is a primary key different from a unique key?",
                "is_follow_up": True,
            },
            {
                "scores": {"correctness": 50, "depth": 40, "clarity": 75, "relevance": 80},
                "feedback": "The distinction is closer, but the example is thin.",
                "next_question": None,
                "is_follow_up": False,
            },
            {
                "strengths": ["Clear wording"],
                "improvements": ["Revise primary key constraints"],
                "weak_areas": ["Keys"],
            },
        ],
    )
    rejected = client.post(
        "/api/v1/interviews",
        json={"kind": "technical", "topic": "Cooking", "difficulty": "beginner"},
        headers=auth_header(token),
    )
    assert rejected.status_code == 422
    started = client.post(
        "/api/v1/interviews",
        json={"kind": "technical", "topic": "SQL", "difficulty": "beginner"},
        headers=auth_header(token),
    )
    session_id = started.get_json()["id"]
    client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"answer": "A primary key identifies a row."},
        headers=auth_header(token),
    )
    client.post(
        f"/api/v1/interviews/{session_id}/answers",
        json={"answer": "A unique key can allow one null, depending on the database."},
        headers=auth_header(token),
    )
    finished = client.post(f"/api/v1/interviews/{session_id}/complete", headers=auth_header(token))
    body = finished.get_json()
    assert body["topic"] == "SQL"
    assert body["difficulty"] == "beginner"
    assert "Correctness" in body["weak_areas"]
    assert "Depth" in body["weak_areas"]
    assert "SQL" in body["weak_areas"]
    history = client.get("/api/v1/interviews", headers=auth_header(token))
    assert history.get_json()["total"] == 1
    assert "turns" not in history.get_json()["items"][0]


def test_practice_routes_are_private_to_the_student(client, app):
    owner = register(client, email="owner@example.com", roll_number="CS015")
    other = register(client, email="other@example.com", roll_number="CS016")
    uploaded = upload(client, owner, docx_bytes(RICH_LINES), "ada.docx")
    resume_id = uploaded.get_json()["id"]
    hidden = client.get(f"/api/v1/resumes/{resume_id}", headers=auth_header(other))
    assert hidden.status_code == 404
    tpo = register_tpo(client)
    forbidden = client.post(
        "/api/v1/interviews",
        json={"kind": "hr"},
        headers=auth_header(tpo.get_json()["access_token"]),
    )
    assert forbidden.status_code == 403
    assert app.extensions.get("llm") is None

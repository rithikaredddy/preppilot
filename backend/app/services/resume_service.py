import re
import uuid
from decimal import Decimal
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from sqlalchemy import select

from app.errors import ApiError
from app.extensions import db
from app.models.practice import Resume, ResumeAnalysis
from app.models.user import User
from app.services import scoring
from app.services.llm import LLMResponseError, complete_json, require_string_list

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
CAMPUS_SKILLS = (
    "Python",
    "Java",
    "SQL",
    "DBMS",
    "Operating Systems",
    "Computer Networks",
    "OOP",
    "Data Structures",
    "Machine Learning",
    "Git",
)
ANALYSIS_INSTRUCTIONS = """
Extract structured facts from the resume text. When a job description is present, list the skills it asks for.
Return one JSON object with exactly these keys:
skills, education, projects, experience, certifications, required_skills, formatting_issues, suggestions.
Each value is an array of short strings.
skills are skills written in the resume.
required_skills are skills explicitly requested by the job description. Use an empty array when no job description is provided.
suggestions must contain 3 to 5 specific actions the student can take.
Do not invent employers, degrees, or scores. Do not return an ATS score or a match percentage.
""".strip()


def save_upload(student: User, upload) -> Resume:
    from flask import current_app

    filename = _safe_filename(upload.filename or "")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_TYPES:
        raise ApiError(415, "unsupported_file", "Upload a PDF or DOCX resume.")
    max_bytes = int(current_app.config["MAX_UPLOAD_BYTES"])
    content = upload.stream.read(max_bytes + 1)
    if not content:
        raise ApiError(400, "empty_file", "The file is empty.")
    if len(content) > max_bytes:
        raise ApiError(413, "file_too_large", "Resume files must be 5 MB or smaller.")
    if not _matches_type(content, suffix):
        raise ApiError(415, "unsupported_file", "That file is not a readable PDF or DOCX.")

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid.uuid4()}{suffix}"
    stored_path.write_bytes(content)
    text = extract_text(stored_path, suffix)
    if len(text.strip()) < 40:
        stored_path.unlink(missing_ok=True)
        raise ApiError(422, "no_text", "No readable text was found in that file.")

    resume = Resume(
        student_id=student.id,
        original_filename=filename,
        stored_path=str(stored_path),
        mime_type=ALLOWED_TYPES[suffix],
        file_size_bytes=len(content),
        extracted_text=text,
    )
    db.session.add(resume)
    db.session.commit()
    return resume


def analyze(
    student: User, resume: Resume, target_role: str, job_description: str
) -> ResumeAnalysis:
    parsed, provider, model = complete_json(
        ANALYSIS_INSTRUCTIONS,
        {
            "target_role": target_role,
            "job_description": job_description,
            "resume_text": resume.extracted_text[:12000],
        },
    )
    skills = require_string_list(parsed, "skills", max_items=40)
    education = require_string_list(parsed, "education")
    projects = require_string_list(parsed, "projects")
    experience = require_string_list(parsed, "experience")
    certifications = require_string_list(parsed, "certifications")
    model_required = require_string_list(parsed, "required_skills", max_items=40)
    formatting_issues = require_string_list(parsed, "formatting_issues")
    suggestions = require_string_list(parsed, "suggestions", min_items=1, max_items=6)
    required = required_skills(job_description, model_required)
    missing = [
        skill for skill in required if not skill_present(skill, skills, resume.extracted_text)
    ]
    match = round(100 * (len(required) - len(missing)) / len(required), 2)
    ats = ats_score(resume.extracted_text, formatting_issues)
    analysis = ResumeAnalysis(
        resume_id=resume.id,
        student_id=student.id,
        target_role=target_role.strip(),
        job_description_text=job_description.strip(),
        ats_score=Decimal(f"{ats:.2f}"),
        skill_match_percentage=Decimal(f"{match:.2f}"),
        skills=skills,
        education=education,
        projects=projects,
        experience=experience,
        certifications=certifications,
        missing_skills=missing,
        formatting_issues=formatting_issues,
        suggestions=suggestions,
        provider=provider,
        model_name=model,
    )
    db.session.add(analysis)
    db.session.flush()
    scoring.record_score(
        student.id,
        "resume",
        ats,
        "resume_analysis",
        analysis.id,
        suggestions[:3],
        missing[:5],
    )
    db.session.commit()
    return analysis


def ats_score(text: str, formatting_issues: list[str]) -> float:
    """Score resume structure from the extracted file, not from a fixed number.

    Contact details, recognizable sections, length, and bullet lines add points.
    Each formatting issue reported by the model removes 4 points, up to 20.
    This is a placement-prep heuristic, not a commercial ATS score.
    """
    lowered = text.lower()
    score = 20.0
    if re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", text, flags=re.IGNORECASE):
        score += 10
    if re.search(r"(?:\+?\d[\d\s-]{8,}\d)", text):
        score += 5
    for label, points in (
        ("education", 15),
        ("skill", 15),
        ("project", 15),
        ("experience", 10),
    ):
        if label in lowered:
            score += points
    length = len(text.strip())
    if 400 <= length <= 6000:
        score += 10
    elif length >= 150:
        score += 5
    bullets = len(re.findall(r"(?m)^[\s]*([-•*]|\d+\.)\s+\S", text))
    if bullets >= 3:
        score += 10
    score -= min(20, 4 * len(formatting_issues))
    return float(max(0, min(100, round(score, 2))))


def required_skills(job_description: str, model_required: list[str]) -> list[str]:
    if not job_description.strip():
        return list(CAMPUS_SKILLS)
    found: list[str] = []
    seen: set[str] = set()
    supplemented = [skill for skill in CAMPUS_SKILLS if mentioned(skill, job_description)]
    for skill in [*model_required, *supplemented]:
        key = _normalize(skill)
        if key and key not in seen:
            seen.add(key)
            found.append(skill.strip())
    if not found:
        raise LLMResponseError("The model did not identify skills in the job description.")
    return found


def skill_present(skill: str, extracted: list[str], resume_text: str) -> bool:
    if any(_same_skill(skill, item) for item in extracted):
        return True
    return mentioned(skill, resume_text)


def mentioned(skill: str, text: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def list_resumes(student: User) -> list[Resume]:
    return list(
        db.session.scalars(
            select(Resume).where(Resume.student_id == student.id).order_by(Resume.created_at.desc())
        )
    )


def get_resume(student: User, resume_id) -> Resume:
    resume = db.session.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise ApiError(404, "not_found", "That resume was not found.")
    return resume


def get_analysis(student: User, analysis_id) -> ResumeAnalysis:
    analysis = db.session.get(ResumeAnalysis, analysis_id)
    if analysis is None or analysis.student_id != student.id:
        raise ApiError(404, "not_found", "That analysis was not found.")
    return analysis


def public_resume(resume: Resume, *, preview: bool = False) -> dict:
    latest = latest_analysis(resume)
    payload = {
        "id": str(resume.id),
        "original_filename": resume.original_filename,
        "file_size_bytes": resume.file_size_bytes,
        "created_at": resume.created_at,
        "latest_analysis": public_analysis(latest) if latest else None,
    }
    if preview:
        payload["extracted_preview"] = resume.extracted_text[:1200]
        payload["character_count"] = len(resume.extracted_text)
    return payload


def public_analysis(analysis: ResumeAnalysis) -> dict:
    return {
        "id": str(analysis.id),
        "resume_id": str(analysis.resume_id),
        "target_role": analysis.target_role,
        "job_description": analysis.job_description_text,
        "ats_score": float(analysis.ats_score),
        "skill_match_percentage": float(analysis.skill_match_percentage),
        "skills": analysis.skills,
        "education": analysis.education,
        "projects": analysis.projects,
        "experience": analysis.experience,
        "certifications": analysis.certifications,
        "missing_skills": analysis.missing_skills,
        "formatting_issues": analysis.formatting_issues,
        "suggestions": analysis.suggestions,
        "provider": analysis.provider,
        "model_name": analysis.model_name,
        "created_at": analysis.created_at,
    }


def latest_analysis(resume: Resume) -> ResumeAnalysis | None:
    if not resume.analyses:
        return None
    return max(resume.analyses, key=lambda item: item.created_at)


def build_report(analysis: ResumeAnalysis):
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    resume = db.session.get(Resume, analysis.resume_id)
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, title="Resume analysis"
    )
    story = [
        Paragraph("Resume analysis", styles["Title"]),
        Paragraph(_xml(resume.original_filename if resume else "Resume"), styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"Target role: {_xml(analysis.target_role)}", styles["Normal"]),
        Paragraph(f"ATS-style score: {float(analysis.ats_score):.0f} / 100", styles["Normal"]),
        Paragraph(f"Skill match: {float(analysis.skill_match_percentage):.0f}%", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(
            "The ATS-style score checks contact details, section headings, length, and bullet lines in the uploaded file, then subtracts points for formatting issues. It is not a commercial ATS score. The skill match is the overlap between skills found in the resume and the skills requested by the job description.",
            styles["Normal"],
        ),
    ]
    _section(story, styles, "Skills found", analysis.skills)
    _section(story, styles, "Missing skills", analysis.missing_skills)
    _section(story, styles, "Education", analysis.education)
    _section(story, styles, "Projects", analysis.projects)
    _section(story, styles, "Experience", analysis.experience)
    _section(story, styles, "Certifications", analysis.certifications)
    _section(story, styles, "Formatting issues", analysis.formatting_issues)
    _section(story, styles, "Suggestions", analysis.suggestions)
    document.build(story)
    buffer.seek(0)
    return buffer


def extract_text(path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if suffix == ".docx":
        document = Document(str(path))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" ".join(cell.text for cell in row.cells))
        return "\n".join(parts).strip()
    raise ApiError(415, "unsupported_file", "Upload a PDF or DOCX resume.")


def _section(story, styles, title: str, items: list) -> None:
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Spacer

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(_xml(title), styles["Heading2"]))
    if not items:
        story.append(Paragraph("None recorded.", styles["Normal"]))
        return
    for item in items:
        story.append(Paragraph(f"• {_xml(str(item))}", styles["Normal"]))


def _xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "resume"
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "", name)
    return (cleaned or "resume")[:180]


def _matches_type(content: bytes, suffix: str) -> bool:
    if suffix == ".pdf":
        return content.startswith(b"%PDF")
    if suffix == ".docx":
        return content.startswith(b"PK")
    return False


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _same_skill(left: str, right: str) -> bool:
    a = _normalize(left)
    b = _normalize(right)
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) < 3 or len(b) < 3:
        return False
    return a in b or b in a

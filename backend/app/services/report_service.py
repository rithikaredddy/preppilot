"""Downloadable placement performance report."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select

from app.errors import ApiError
from app.extensions import db
from app.models.insights import Report
from app.models.practice import InterviewSession, ResumeAnalysis
from app.models.user import User
from app.services.analytics import analytics
from app.services.readiness import live_snapshot

NAVY = colors.HexColor("#1A3348")
PAPER = colors.HexColor("#F3F0E8")
INK = colors.HexColor("#1C1915")


def build_for(student: User):
    profile = student.student_profile
    if profile is None:
        raise ApiError(404, "profile_missing", "This account has no profile.")
    view = analytics(student.id)
    snapshot = live_snapshot(student.id)
    if snapshot is None and not any(item["score"] is not None for item in view["scores"]):
        raise ApiError(
            422,
            "not_enough_activity",
            "Complete at least one activity before downloading a report.",
        )
    suggestions = _suggestions(student.id, view)
    story = _story(profile.full_name, profile.branch, profile.roll_number, view, snapshot, suggestions)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Placement performance report",
    )
    document.build(story)
    buffer.seek(0)
    folder = Path(current_app.config["UPLOAD_DIR"]) / "reports"
    folder.mkdir(parents=True, exist_ok=True)
    stored = folder / f"{student.id}.pdf"
    stored.write_bytes(buffer.getvalue())
    db.session.add(Report(student_id=student.id, pdf_path=str(stored)))
    db.session.commit()
    buffer.seek(0)
    return buffer


def _story(name, branch, roll, view, snapshot, suggestions):
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=NAVY,
        fontSize=22,
        leading=26,
        spaceAfter=4,
    )
    section = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading2"],
        textColor=NAVY,
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
    )
    body = ParagraphStyle("ReportBody", parent=styles["Normal"], textColor=INK, fontSize=10, leading=14)
    muted = ParagraphStyle("ReportMuted", parent=body, textColor=colors.HexColor("#5F584E"))
    story = [
        Paragraph("Placement performance report", title),
        Paragraph(escape(f"{name} · {branch} · {roll}"), muted),
        Spacer(1, 8),
    ]
    if snapshot is not None:
        story.append(
            Paragraph(
                escape(
                    f"Placement readiness: {snapshot['readiness_percentage']:.0f}%. {snapshot['headline']}"
                ),
                body,
            )
        )
        story.append(Spacer(1, 6))
    score_rows = [["Area", "Score"]]
    for item in view["scores"]:
        shown = "Not recorded" if item["score"] is None else f"{item['score']:.0f}"
        score_rows.append([item["label"], shown])
    table = Table(score_rows, colWidths=[110 * mm, 50 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), PAPER),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([Paragraph("Scores", section), table])
    if view["domains"]:
        story.append(Paragraph("Technical domains", section))
        for domain in view["domains"]:
            story.append(
                Paragraph(
                    escape(f"{domain['domain']}: {domain['score']:.0f} across {domain['sessions']} session(s)"),
                    body,
                )
            )
    if view["weak_areas"]:
        story.append(Paragraph("Areas below 60", section))
        for area in view["weak_areas"]:
            story.append(Paragraph(escape(f"{area['label']}: {area['score']:.0f}"), body))
    story.append(Paragraph("Suggestions", section))
    if suggestions:
        for line in suggestions:
            story.append(Paragraph(f"• {escape(line)}", body))
    else:
        story.append(Paragraph("No suggestions are stored yet.", body))
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "Readiness is estimated by a Random Forest trained on synthetic, correlated placement data. It is a preparation signal, not an offer prediction.",
            muted,
        )
    )
    return story


def _suggestions(student_id, view) -> list[str]:
    lines: list[str] = []
    analysis = db.session.scalar(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.student_id == student_id)
        .order_by(ResumeAnalysis.created_at.desc())
    )
    if analysis is not None:
        lines.extend(str(item) for item in (analysis.suggestions or [])[:3])
    session = db.session.scalar(
        select(InterviewSession)
        .where(
            InterviewSession.student_id == student_id,
            InterviewSession.status == "completed",
        )
        .order_by(InterviewSession.completed_at.desc())
    )
    if session is not None and session.improvements:
        lines.extend(str(item) for item in session.improvements[:3])
    for area in view["weak_areas"]:
        lines.append(f"Raise {area['label'].lower()} above 60. It is {area['score']:.0f} now.")
    deduped = []
    for line in lines:
        if line and line not in deduped:
            deduped.append(line)
    return deduped[:8]

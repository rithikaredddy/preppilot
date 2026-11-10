from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.extensions import db
from app.models.practice import InterviewSession, PerformanceEvent, PerformanceSummary
from app.models.user import utcnow

CATEGORIES = ("resume", "hr", "technical", "coding", "communication")


def record_score(
    student_id: UUID,
    category: str,
    score: float,
    source_type: str,
    source_id: UUID,
    strengths: list[str],
    weaknesses: list[str],
) -> None:
    """Append a score event and update the student's latest category score."""
    db.session.add(
        PerformanceEvent(
            student_id=student_id,
            category=category,
            score=_decimal(score),
            source_type=source_type,
            source_id=source_id,
        )
    )
    summary = db.session.get(PerformanceSummary, student_id)
    if summary is None:
        summary = PerformanceSummary(student_id=student_id, strengths={}, weaknesses={})
        db.session.add(summary)
    setattr(summary, f"{category}_score", _decimal(score))
    stored_strengths = dict(summary.strengths or {})
    stored_weaknesses = dict(summary.weaknesses or {})
    stored_strengths[category] = strengths
    stored_weaknesses[category] = weaknesses
    summary.strengths = stored_strengths
    summary.weaknesses = stored_weaknesses
    summary.updated_at = utcnow()


def dashboard_summary(student_id: UUID) -> dict:
    summary = db.session.get(PerformanceSummary, student_id)
    completed = db.session.scalar(
        select(func.count())
        .select_from(InterviewSession)
        .where(
            InterviewSession.student_id == student_id,
            InterviewSession.status == "completed",
        )
    )
    payload = {
        f"{category}_score": _float(getattr(summary, f"{category}_score", None))
        if summary is not None
        else None
        for category in CATEGORIES
    }
    payload["completed_sessions"] = int(completed or 0)
    return payload


def _decimal(score: float) -> Decimal:
    return Decimal(f"{round(score, 2):.2f}")


def _float(value) -> float | None:
    if value is None:
        return None
    return float(value)

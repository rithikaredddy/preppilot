"""Student analytics and TPO batch views. No interview transcripts leave this module."""

from uuid import UUID

from sqlalchemy import func, select

from app.errors import ApiError
from app.extensions import db
from app.models.insights import RoadmapItem
from app.models.practice import InterviewSession, PerformanceEvent, PerformanceSummary
from app.models.user import StudentProfile, User
from app.services.readiness import live_snapshot

CATEGORY_LABELS = {
    "resume": "Resume",
    "hr": "HR interview",
    "technical": "Technical interview",
    "coding": "Coding",
    "communication": "Communication",
}
WEAK_BELOW = 60
STRONG_FROM = 75


def analytics(student_id: UUID) -> dict:
    summary = db.session.get(PerformanceSummary, student_id)
    scores = [
        {
            "category": key,
            "label": CATEGORY_LABELS[key],
            "score": _float(getattr(summary, f"{key}_score", None)) if summary else None,
        }
        for key in CATEGORY_LABELS
    ]
    measured = [item for item in scores if item["score"] is not None]
    weak = [item for item in measured if item["score"] < WEAK_BELOW]
    strong = [item for item in measured if item["score"] >= STRONG_FROM]
    events = db.session.scalars(
        select(PerformanceEvent)
        .where(PerformanceEvent.student_id == student_id)
        .order_by(PerformanceEvent.recorded_at.asc())
        .limit(60)
    )
    timeline = [
        {
            "recorded_at": event.recorded_at,
            "category": event.category,
            "label": CATEGORY_LABELS.get(event.category, event.category),
            "score": float(event.score),
        }
        for event in events
    ]
    domain_rows = db.session.execute(
        select(
            InterviewSession.topic,
            func.avg(InterviewSession.overall_score),
            func.count(),
        )
        .where(
            InterviewSession.student_id == student_id,
            InterviewSession.kind == "technical",
            InterviewSession.status == "completed",
            InterviewSession.overall_score.is_not(None),
        )
        .group_by(InterviewSession.topic)
    ).all()
    domains = [
        {
            "domain": topic or "General",
            "score": round(float(average), 2),
            "sessions": int(count),
        }
        for topic, average, count in domain_rows
    ]
    items = list(
        db.session.scalars(select(RoadmapItem).where(RoadmapItem.student_id == student_id))
    )
    completed = sum(1 for item in items if item.is_complete)
    if weak:
        base_gap = round(sum(100 - item["score"] for item in weak) / len(weak), 2)
    else:
        base_gap = 0.0
    reduction = min(base_gap, completed * 6)
    return {
        "scores": scores,
        "timeline": timeline,
        "domains": domains,
        "weak_areas": weak,
        "strong_areas": strong,
        "gap": {
            "base_gap": base_gap,
            "remaining_gap": round(base_gap - reduction, 2),
            "completed_items": completed,
            "total_items": len(items),
        },
    }


def student_rows(branch: str) -> list[tuple[User, StudentProfile, dict | None]]:
    filters = [User.role == "student", User.is_active.is_(True)]
    if branch.strip():
        filters.append(func.lower(StudentProfile.branch) == branch.strip().lower())
    rows = db.session.execute(
        select(User, StudentProfile)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .where(*filters)
    ).all()
    enriched = []
    for user, profile in rows:
        enriched.append((user, profile, live_snapshot(user.id)))
    return enriched


def list_for_tpo(*, page: int, page_size: int, branch: str, sort: str, readiness_below) -> dict:
    items = [_student_item(user, profile, snapshot) for user, profile, snapshot in student_rows(branch)]
    if readiness_below is not None:
        items = [
            item
            for item in items
            if item["readiness_percentage"] is not None
            and item["readiness_percentage"] < readiness_below
        ]
    if sort == "readiness":
        items.sort(
            key=lambda item: (
                item["readiness_percentage"] is None,
                -(item["readiness_percentage"] or 0),
            )
        )
    elif sort == "branch":
        items.sort(key=lambda item: (item["branch"].lower(), item["roll_number"]))
    elif sort == "roll_number":
        items.sort(key=lambda item: item["roll_number"])
    else:
        items.sort(key=lambda item: item["full_name"].lower())
    total = len(items)
    start = (page - 1) * page_size
    return {
        "items": items[start : start + page_size],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def batch_insights(branch: str) -> dict:
    grouped: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    weak_counts: dict[str, int] = {}
    below = 0
    rows = student_rows(branch)
    for user, profile, snapshot in rows:
        counts[profile.branch] = counts.get(profile.branch, 0) + 1
        grouped.setdefault(profile.branch, [])
        if snapshot is None:
            continue
        grouped[profile.branch].append(snapshot["readiness_percentage"])
        if snapshot["readiness_percentage"] < WEAK_BELOW:
            below += 1
        summary = db.session.get(PerformanceSummary, user.id)
        if summary is None:
            continue
        for key, label in CATEGORY_LABELS.items():
            score = _float(getattr(summary, f"{key}_score"))
            if score is not None and score < WEAK_BELOW:
                weak_counts[label] = weak_counts.get(label, 0) + 1
    averages = [
        {
            "branch": name,
            "average_readiness": round(sum(values) / len(values), 2) if values else None,
            "student_count": counts.get(name, 0),
        }
        for name, values in sorted(grouped.items())
    ]
    common = [
        {"area": area, "student_count": count}
        for area, count in sorted(weak_counts.items(), key=lambda item: item[1], reverse=True)
    ]
    return {
        "student_count": len(rows),
        "below_threshold_count": below,
        "threshold": WEAK_BELOW,
        "branch_averages": averages,
        "common_weak_areas": common[:6],
    }


def student_detail(student_id: UUID) -> dict:
    user = db.session.get(User, student_id)
    profile = user.student_profile if user is not None else None
    if user is None or user.role != "student" or profile is None or not user.is_active:
        raise ApiError(404, "not_found", "That student was not found.")
    snapshot = live_snapshot(user.id)
    view = analytics(user.id)
    return {
        "id": str(user.id),
        "full_name": profile.full_name,
        "email": user.email,
        "roll_number": profile.roll_number,
        "branch": profile.branch,
        "graduation_year": profile.graduation_year,
        "cgpa": float(profile.cgpa) if profile.cgpa is not None else None,
        "readiness_percentage": None if snapshot is None else snapshot["readiness_percentage"],
        "headline": None if snapshot is None else snapshot["headline"],
        "scores": view["scores"],
        "weak_areas": view["weak_areas"],
        "strong_areas": view["strong_areas"],
        "domains": view["domains"],
    }


def _student_item(user: User, profile: StudentProfile, snapshot: dict | None) -> dict:
    top = None
    if snapshot and snapshot["top_factors"]:
        weakest = [
            factor for factor in snapshot["top_factors"] if factor.get("student_score") is not None
        ]
        weakest.sort(key=lambda factor: factor["student_score"])
        top = weakest[0]["label"] if weakest else snapshot["top_factors"][0]["label"]
    return {
        "id": str(user.id),
        "full_name": profile.full_name,
        "email": user.email,
        "roll_number": profile.roll_number,
        "branch": profile.branch,
        "graduation_year": profile.graduation_year,
        "readiness_percentage": None if snapshot is None else snapshot["readiness_percentage"],
        "top_factor": top,
    }


def _float(value) -> float | None:
    if value is None:
        return None
    return float(value)


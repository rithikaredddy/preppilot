"""Personalized roadmap from weak areas and the readiness model's top factors."""

import time
from uuid import UUID

from sqlalchemy import select

from app.errors import ApiError
from app.extensions import db
from app.models.insights import RoadmapItem
from app.models.user import User
from app.services.analytics import analytics
from app.services.llm import LLMResponseError, complete_json
from app.services.readiness import live_snapshot

PLAN_INSTRUCTIONS = """
You are a placement coach. Write a 7-day study plan from this student's scores.
Spend more days on the lowest scores. Do not give the same task every day.
Return JSON with one key, items, an array of exactly 7 objects in day order.
Each object has day (1 through 7), task, minutes, focus, resource_title, resource_link.
task is one concrete session, such as "Solve 2 easy array problems, then rewrite the failing one."
minutes is an integer from 30 to 90.
focus is one of resume, interview, coding, communication.
resource_link is a full https URL to a free article or practice set for that day.
Use only the scores and weak areas in the payload. No motivational filler.
""".strip()

DEFAULT_LINKS = {
    "coding": ("LeetCode problem set", "https://leetcode.com/problemset/"),
    "interview": ("Placement interview notes", "https://www.geeksforgeeks.org/interview-experiences/"),
    "communication": ("STAR answer structure", "https://www.themuse.com/advice/star-interview-method"),
    "resume": ("Engineer resume guide", "https://www.geeksforgeeks.org/blogs/how-to-write-a-resume-for-software-engineer/"),
}

LIBRARY = {
    "coding": [
        (
            "DSA",
            "Two pointers on arrays and strings",
            "Array practice in the two-pointer pattern",
            "https://leetcode.com/tag/two-pointers/",
            "coding",
        ),
        (
            "DSA",
            "Hash maps for counts and anagrams",
            "Hash-table practice problems",
            "https://leetcode.com/tag/hash-table/",
            "coding",
        ),
        (
            "DSA",
            "Binary search on a sorted range",
            "Binary search explained with examples",
            "https://www.geeksforgeeks.org/binary-search/",
            "coding",
        ),
    ],
    "technical": [
        (
            "DBMS",
            "Normalization and keys",
            "Normalization walkthrough",
            "https://www.geeksforgeeks.org/dbms/introduction-of-database-normalization/",
            "interview",
        ),
        (
            "OS",
            "Processes, threads, and scheduling",
            "Operating system process notes",
            "https://www.geeksforgeeks.org/operating-systems/introduction-of-process-management/",
            "interview",
        ),
    ],
    "hr": [
        (
            "HR",
            "A specific introduction with one project",
            "How to structure a one-minute introduction",
            "https://www.geeksforgeeks.org/interview-experiences/self-introduction-for-interview/",
            "interview",
        )
    ],
    "communication": [
        (
            "Communication",
            "Shorter answers with one concrete example",
            "STAR method for behavioral answers",
            "https://www.themuse.com/advice/star-interview-method",
            "communication",
        )
    ],
    "resume": [
        (
            "Resume",
            "Measurable bullets for projects",
            "Resume bullet examples for engineers",
            "https://www.geeksforgeeks.org/blogs/how-to-write-a-resume-for-software-engineer/",
            "resume",
        )
    ],
}

_recent: dict[str, float] = {}


def list_items(student: User) -> dict:
    rows = db.session.scalars(
        select(RoadmapItem)
        .where(RoadmapItem.student_id == student.id)
        .order_by(RoadmapItem.created_at.asc())
    )
    items = [_public(row) for row in rows]
    view = analytics(student.id)
    return {"items": items, "gap": view["gap"], "source": None, "note": None}


def generate(student: User) -> dict:
    _throttle(student.id)
    view = analytics(student.id)
    snapshot = live_snapshot(student.id)
    if not view["weak_areas"] and snapshot is None:
        raise ApiError(
            422,
            "not_enough_activity",
            "Finish a resume review, interview, or coding problem before building a roadmap.",
        )
    source = "rules"
    note = None
    drafted = _from_rules(view, snapshot)
    try:
        parsed, _provider, _model = complete_json(
            PLAN_INSTRUCTIONS,
            {
                "scores": view["scores"],
                "weak_areas": view["weak_areas"],
                "strong_areas": view["strong_areas"],
                "domains": view["domains"],
                "readiness": None if snapshot is None else snapshot["readiness_percentage"],
                "headline": None if snapshot is None else snapshot["headline"],
                "top_factors": None if snapshot is None else snapshot["top_factors"],
            },
        )
        drafted = _from_model(parsed)
        source = "llm"
    except LLMResponseError:
        note = "The study plan was built from your weak areas because the model response could not be read."
    except ApiError as exc:
        if exc.error_code not in {"llm_not_configured", "llm_provider_error", "llm_response_invalid"}:
            raise
        note = (
            "The study plan was built from your weak areas because the language model "
            "could not be reached."
        )

    db.session.query(RoadmapItem).filter(RoadmapItem.student_id == student.id).delete(
        synchronize_session=False
    )
    for item in drafted:
        db.session.add(RoadmapItem(student_id=student.id, **item))
    db.session.commit()
    payload = list_items(student)
    payload["source"] = source
    payload["note"] = note
    return payload


def set_complete(student: User, item_id: UUID, is_complete: bool) -> dict:
    row = db.session.get(RoadmapItem, item_id)
    if row is None or row.student_id != student.id:
        raise ApiError(404, "not_found", "That roadmap item was not found.")
    row.is_complete = is_complete
    db.session.commit()
    return _public(row)


def _from_model(parsed: dict) -> list[dict]:
    raw = parsed.get("items")
    if not isinstance(raw, list):
        raise LLMResponseError("The model response is missing items.")
    items = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        day = entry.get("day")
        if isinstance(day, bool) or not isinstance(day, int) or day < 1 or day > 14:
            continue
        task = _text(entry.get("task") or entry.get("subtopic"))
        focus = _text(entry.get("focus")) or "coding"
        if focus not in DEFAULT_LINKS:
            focus = "coding"
        title = _text(entry.get("resource_title")) or DEFAULT_LINKS[focus][0]
        link = _text(entry.get("resource_link"))
        if not link.startswith("http"):
            link = DEFAULT_LINKS[focus][1]
        minutes = entry.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            minutes = 45
        minutes = max(20, min(minutes, 120))
        if not task:
            continue
        items.append(
            {
                "topic": f"Day {day}",
                "subtopic": f"{minutes} min · {task}"[:240],
                "resource_title": title[:240],
                "resource_link": link[:500],
                "focus": focus,
            }
        )
    if len(items) < 5:
        raise LLMResponseError("The model response did not include a daily plan.")
    items.sort(key=lambda item: int(item["topic"].split()[-1]))
    return items[:7]


def _from_rules(view: dict, snapshot: dict | None) -> list[dict]:
    """Day-by-day plan used when the language model cannot be reached."""
    pool = []
    seen = set()
    order = [item["category"] for item in sorted(view["weak_areas"], key=lambda row: row["score"])]
    if snapshot is not None and snapshot["top_factors"]:
        lead = snapshot["top_factors"][0]["feature"]
        mapped = {
            "coding_score": "coding",
            "resume_ats": "resume",
            "interview_score": "technical",
            "communication_score": "communication",
        }.get(lead)
        if mapped and mapped not in order:
            order.insert(0, mapped)
    if not order:
        order = ["coding", "technical", "hr"]
    for category in order:
        for row in LIBRARY.get(category, []):
            if row[1] in seen:
                continue
            seen.add(row[1])
            pool.append(row)
    while len(pool) < 7:
        pool.append(LIBRARY["coding"][len(pool) % len(LIBRARY["coding"])])
    days = []
    for index, row in enumerate(pool[:7], start=1):
        minutes = 60 if index <= 5 else 40
        days.append(
            {
                "topic": f"Day {index}",
                "subtopic": f"{minutes} min · {row[1]}"[:240],
                "resource_title": row[2],
                "resource_link": row[3],
                "focus": row[4],
            }
        )
    return days


def _public(row: RoadmapItem) -> dict:
    return {
        "id": str(row.id),
        "topic": row.topic,
        "subtopic": row.subtopic,
        "resource_title": row.resource_title,
        "resource_link": row.resource_link,
        "focus": row.focus,
        "is_complete": row.is_complete,
        "created_at": row.created_at,
    }


def _text(value) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _throttle(student_id: UUID) -> None:
    now = time.monotonic()
    previous = _recent.get(str(student_id), 0)
    if now - previous < 12:
        raise ApiError(429, "rate_limited", "Wait a few seconds before generating another roadmap.")
    _recent[str(student_id)] = now

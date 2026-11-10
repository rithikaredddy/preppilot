from decimal import Decimal

from sqlalchemy import func, select

from app.errors import ApiError
from app.extensions import db
from app.models.practice import InterviewSession, InterviewTurn, Resume
from app.models.user import User, utcnow
from app.services import scoring
from app.services.llm import complete_json, require_score, require_string_list, require_text

MAX_TURNS = 4
MIN_ANSWERS = 2
TECHNICAL_TOPICS = (
    "Java",
    "Python",
    "SQL",
    "DBMS",
    "OS",
    "Computer Networks",
    "OOP",
    "DSA",
    "ML",
)
DIFFICULTIES = ("beginner", "intermediate", "advanced")
HR_DIMENSIONS = ("language_specificity", "communication", "relevance", "professionalism")
TECHNICAL_DIMENSIONS = ("correctness", "depth", "clarity", "relevance")
DIMENSION_LABELS = {
    "language_specificity": "Confidence-related language",
    "communication": "Communication",
    "relevance": "Relevance",
    "professionalism": "Professionalism",
    "correctness": "Correctness",
    "depth": "Depth",
    "clarity": "Clarity",
}

QUESTION_INSTRUCTIONS = """
You are a campus placement interviewer. Ask exactly one question.
For an HR interview, start with a common placement question about the student's background, teamwork, or a decision.
For a technical interview, follow question_style.
When question_style is "coding", ask the student to write code, a SQL query, or complete a short function on the given topic and difficulty. Put the full problem in the question. Do not ask only for a definition.
When question_style is "concept", ask a concept or reasoning question on that topic and difficulty.
Return JSON: {"question": "one question", "is_follow_up": false}.
""".strip()

ANSWER_INSTRUCTIONS = """
Evaluate the student's latest answer and, when useful, write one follow-up question.
Return JSON with keys scores, feedback, next_question, and is_follow_up.
scores is an object whose keys are exactly the requested dimension names. Each score is a number from 0 to 100.
feedback is two sentences about this answer.
next_question is one follow-up that refers to a specific detail in the answer, or null when the answer needs no follow-up or the interview has reached its last turn.
is_follow_up is true only when next_question reacts to the answer.
For HR, language_specificity scores how specific, structured, and definite the wording is. It is not a voice, face, or emotion score.
When question_style is "coding", score correctness from the code or query in the answer, and make next_question another short coding task or a fix to the code they wrote.
When question_style is "concept", ask a concept follow-up.
Do not return an overall interview score.
""".strip()

SUMMARY_INSTRUCTIONS = """
Write the closing narrative for a finished interview using only the supplied turn feedback and scores.
Return JSON with keys strengths, improvements, and weak_areas.
Each value is an array of 2 to 4 short strings.
Do not invent a numeric overall score.
""".strip()


def start_session(student: User, data: dict) -> InterviewSession:
    kind = data["kind"]
    topic = None
    difficulty = None
    if kind == "technical":
        topic = data.get("topic")
        difficulty = data.get("difficulty")
        if topic not in TECHNICAL_TOPICS:
            raise ApiError(422, "validation_error", "Choose one of the placement topics.")
        if difficulty not in DIFFICULTIES:
            raise ApiError(422, "validation_error", "Choose beginner, intermediate, or advanced.")
    resume = _owned_resume(student, data.get("resume_id"))
    parsed, _provider, _model = complete_json(
        QUESTION_INSTRUCTIONS,
        _context(student, kind, topic, difficulty, resume, turns=[], answer=None),
    )
    question = require_text(parsed, "question", max_length=1500)
    session = InterviewSession(
        student_id=student.id,
        kind=kind,
        topic=topic,
        difficulty=difficulty,
        resume_id=resume.id if resume else None,
        status="in_progress",
    )
    session.turns.append(InterviewTurn(turn_index=1, question_text=question, is_follow_up=False))
    db.session.add(session)
    db.session.commit()
    return _reload(session)


def submit_answer(student: User, session: InterviewSession, answer: str) -> InterviewSession:
    if session.status != "in_progress":
        raise ApiError(409, "interview_closed", "This interview is already finished.")
    turns = _turns(session)
    open_turn = next((turn for turn in turns if turn.answer_text is None), None)
    if open_turn is None:
        raise ApiError(409, "no_open_question", "There is no open question to answer.")
    if len(turns) > MAX_TURNS:
        raise ApiError(409, "interview_full", "Finish this interview to save the result.")
    cleaned = answer.strip()
    if not cleaned:
        raise ApiError(422, "validation_error", "Write an answer before submitting.")
    dimensions = HR_DIMENSIONS if session.kind == "hr" else TECHNICAL_DIMENSIONS
    parsed, _provider, _model = complete_json(
        ANSWER_INSTRUCTIONS,
        {
            **_context(
                student,
                session.kind,
                session.topic,
                session.difficulty,
                _resume(session),
                turns,
                cleaned,
            ),
            "question": open_turn.question_text,
            "dimensions": list(dimensions),
            "turns_remaining_after_this": MAX_TURNS - len(turns),
        },
    )
    scores = parsed.get("scores")
    if not isinstance(scores, dict):
        raise ApiError(502, "llm_response_invalid", "The model response is missing scores.")
    evaluation = {
        "scores": {name: require_score(scores, name) for name in dimensions},
        "feedback": require_text(parsed, "feedback"),
    }
    open_turn.answer_text = cleaned
    open_turn.evaluation = evaluation
    next_question = parsed.get("next_question")
    follow_up = (
        isinstance(next_question, str) and bool(next_question.strip()) and len(turns) < MAX_TURNS
    )
    if follow_up:
        session.turns.append(
            InterviewTurn(
                turn_index=open_turn.turn_index + 1,
                question_text=next_question.strip()[:1500],
                is_follow_up=bool(parsed.get("is_follow_up", True)),
            )
        )
    db.session.commit()
    return _reload(session)


def complete_session(student: User, session: InterviewSession) -> InterviewSession:
    if session.status == "completed":
        return session
    if session.status != "in_progress":
        raise ApiError(409, "interview_closed", "This interview is already finished.")
    turns = _turns(session)
    answered = [turn for turn in turns if turn.evaluation]
    if len(answered) < MIN_ANSWERS:
        raise ApiError(
            400,
            "interview_too_short",
            "Answer at least two questions before finishing.",
        )
    dimensions = HR_DIMENSIONS if session.kind == "hr" else TECHNICAL_DIMENSIONS
    dimension_scores = _dimension_averages(answered, dimensions)
    overall = _overall(answered, dimensions)
    parsed, _provider, _model = complete_json(
        SUMMARY_INSTRUCTIONS,
        {
            "kind": session.kind,
            "topic": session.topic,
            "difficulty": session.difficulty,
            "dimension_scores": dimension_scores,
            "turns": [
                {
                    "question": turn.question_text,
                    "answer": turn.answer_text,
                    "scores": (turn.evaluation or {}).get("scores"),
                    "feedback": (turn.evaluation or {}).get("feedback"),
                }
                for turn in answered
            ],
        },
    )
    strengths = require_string_list(parsed, "strengths", min_items=1, max_items=4)
    improvements = require_string_list(parsed, "improvements", min_items=1, max_items=4)
    model_weak = require_string_list(parsed, "weak_areas", min_items=1, max_items=4)
    weak_areas = _weak_areas(session, dimension_scores, model_weak)
    for turn in turns:
        if turn.answer_text is None:
            db.session.delete(turn)
    session.overall_score = Decimal(f"{overall:.2f}")
    session.dimension_scores = dimension_scores
    session.strengths = strengths
    session.improvements = improvements
    session.weak_areas = weak_areas
    session.status = "completed"
    session.completed_at = utcnow()
    scoring.record_score(
        student.id,
        session.kind,
        overall,
        "interview_session",
        session.id,
        strengths,
        weak_areas,
    )
    db.session.commit()
    return _reload(session)


def list_sessions(student: User, page: int, page_size: int) -> dict:
    query = select(InterviewSession).where(InterviewSession.student_id == student.id)
    total = db.session.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.session.scalars(
        query.order_by(InterviewSession.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [public_session(session, include_turns=False) for session in rows],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
    }


def get_session(student: User, session_id) -> InterviewSession:
    session = db.session.get(InterviewSession, session_id)
    if session is None or session.student_id != student.id:
        raise ApiError(404, "not_found", "That interview was not found.")
    return session


def public_session(session: InterviewSession, *, include_turns: bool) -> dict:
    turns = _turns(session)
    payload = {
        "id": str(session.id),
        "kind": session.kind,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "resume_id": str(session.resume_id) if session.resume_id else None,
        "status": session.status,
        "overall_score": float(session.overall_score)
        if session.overall_score is not None
        else None,
        "dimension_scores": session.dimension_scores,
        "strengths": session.strengths,
        "improvements": session.improvements,
        "weak_areas": session.weak_areas,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "turn_count": len(turns),
        "answered_count": sum(1 for turn in turns if turn.answer_text),
        "can_finish": sum(1 for turn in turns if turn.evaluation) >= MIN_ANSWERS
        and session.status == "in_progress",
    }
    if include_turns:
        payload["turns"] = [
            {
                "id": str(turn.id),
                "turn_index": turn.turn_index,
                "question_text": turn.question_text,
                "answer_text": turn.answer_text,
                "is_follow_up": turn.is_follow_up,
                "evaluation": turn.evaluation,
            }
            for turn in turns
        ]
    return payload


def _question_style(kind: str, turns: list) -> str:
    if kind != "technical":
        return "hr"
    answered = sum(1 for turn in turns if turn.answer_text)
    return "coding" if answered % 2 == 0 else "concept"


def _context(student, kind, topic, difficulty, resume, turns, answer):
    profile = student.student_profile
    payload = {
        "kind": kind,
        "topic": topic,
        "difficulty": difficulty,
        "question_style": _question_style(kind, turns),
        "student_name": profile.full_name if profile else "Student",
        "branch": profile.branch if profile else None,
        "prior_turns": [
            {
                "question": turn.question_text,
                "answer": turn.answer_text,
                "is_follow_up": turn.is_follow_up,
            }
            for turn in turns
            if turn.answer_text
        ],
    }
    if answer is not None:
        payload["latest_answer"] = answer
    if resume is not None:
        payload["resume_excerpt"] = resume.extracted_text[:4000]
    return payload


def _owned_resume(student: User, resume_id):
    if resume_id is None:
        return None
    resume = db.session.get(Resume, resume_id)
    if resume is None or resume.student_id != student.id:
        raise ApiError(404, "not_found", "That resume was not found.")
    return resume


def _resume(session: InterviewSession):
    if session.resume_id is None:
        return None
    return db.session.get(Resume, session.resume_id)


def _reload(session: InterviewSession) -> InterviewSession:
    session_id = session.id
    db.session.expire_all()
    reloaded = db.session.get(InterviewSession, session_id)
    if reloaded is None:
        raise ApiError(404, "not_found", "That interview was not found.")
    return reloaded


def _turns(session: InterviewSession) -> list[InterviewTurn]:
    return sorted(session.turns, key=lambda turn: turn.turn_index)


def _dimension_averages(turns: list[InterviewTurn], dimensions) -> dict:
    totals = {name: [] for name in dimensions}
    for turn in turns:
        scores = (turn.evaluation or {}).get("scores") or {}
        for name in dimensions:
            if name in scores:
                totals[name].append(float(scores[name]))
    return {name: round(sum(values) / len(values), 2) for name, values in totals.items() if values}


def _overall(turns: list[InterviewTurn], dimensions) -> float:
    values = []
    for turn in turns:
        scores = (turn.evaluation or {}).get("scores") or {}
        values.extend(float(scores[name]) for name in dimensions if name in scores)
    if not values:
        raise ApiError(409, "interview_unscored", "This interview has no stored scores yet.")
    return round(sum(values) / len(values), 2)


def _weak_areas(
    session: InterviewSession, dimension_scores: dict, model_weak: list[str]
) -> list[str]:
    areas = [
        DIMENSION_LABELS[name]
        for name, score in dimension_scores.items()
        if score < 60 and name in DIMENSION_LABELS
    ]
    if (
        session.kind == "technical"
        and session.topic
        and _overall_from_dimensions(dimension_scores) < 60
    ):
        areas.append(session.topic)
    for item in model_weak:
        if item not in areas:
            areas.append(item)
    return areas[:8]


def _overall_from_dimensions(dimension_scores: dict) -> float:
    if not dimension_scores:
        return 0
    return sum(dimension_scores.values()) / len(dimension_scores)

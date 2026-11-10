import json
import re
import uuid
from io import BytesIO
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.errors import ApiError
from app.extensions import db
from app.models.catalog import CodingSubmission, CommunicationAnalysis
from app.models.practice import InterviewSession, InterviewTurn
from app.models.user import User
from app.services.communication_service import communication_score, count_fillers
from tests.test_auth import auth_header, register_tpo, student_payload

REVIEW = {
    "summary": "The program reads two integers and prints their sum. It matches the public sample.",
    "issues": [],
    "suggestions": ["Name the variables before the split."],
    "time_complexity": "O(1)",
    "space_complexity": "O(1)",
}
TRANSCRIPT = "Um I built the campus portal and explained the database design clearly"


@pytest.fixture(autouse=True)
def clear_overrides(app):
    app.extensions.pop("llm", None)
    app.extensions.pop("code_runner", None)
    app.extensions.pop("transcriber", None)
    yield
    app.extensions.pop("llm", None)
    app.extensions.pop("code_runner", None)
    app.extensions.pop("transcriber", None)


def register(client, **overrides):
    response = client.post("/api/v1/auth/register", json=student_payload(**overrides))
    assert response.status_code == 201
    body = response.get_json()
    return body["access_token"], body["user"]["id"]


def problems(client, token):
    response = client.get("/api/v1/coding/problems", headers=auth_header(token))
    assert response.status_code == 200
    return response.get_json()["items"]


def sum_problem(client, token):
    match = next(item for item in problems(client, token) if item["title"] == "Sum of two integers")
    detail = client.get(f"/api/v1/coding/problems/{match['id']}", headers=auth_header(token))
    assert detail.status_code == 200
    return detail.get_json()


def passing_runner(source_code, language, stdin, _time_limit_ms, _memory_limit_kb):
    if "compile-me" in source_code:
        return {
            "status": "compilation_error",
            "stdout": "",
            "stderr": "error: expected ';'",
            "time_ms": None,
            "memory_kb": None,
        }
    if language == "python" and "a + b" in source_code:
        left, right = map(int, stdin.split())
        return {
            "status": "accepted",
            "stdout": f"{left + right}\n",
            "stderr": "",
            "time_ms": 18,
            "memory_kb": 4100,
        }
    return {
        "status": "accepted",
        "stdout": "0\n",
        "stderr": "",
        "time_ms": 5,
        "memory_kb": 100,
    }


def test_problem_payload_omits_hidden_tests(client):
    token, _student_id = register(client, email="code.hidden@example.com", roll_number="CS501")
    body = sum_problem(client, token)
    text = json.dumps(body)
    assert body["hidden_test_count"] == 1
    assert body["public_tests"][0]["expected_stdout"] == "5\n"
    assert "10 20" not in text
    assert "30\\n" not in text
    assert body["source"] == "curated"
    assert set(body["starter_code"]) == {"python", "java", "cpp"}


def test_python_solution_passes_visible_and_hidden_tests(client, app):
    token, _student_id = register(client, email="code.pass@example.com", roll_number="CS502")
    problem = sum_problem(client, token)
    seen = {}

    def review(_instructions, payload):
        seen["payload"] = payload
        return REVIEW

    app.extensions["code_runner"] = passing_runner
    app.extensions["llm"] = review
    response = client.post(
        f"/api/v1/coding/problems/{problem['id']}/submit",
        headers=auth_header(token),
        json={"language": "python", "source_code": problem["starter_code"]["python"]},
    )
    assert response.status_code == 201
    body = response.get_json()
    text = json.dumps(body)
    assert body["status"] == "accepted"
    assert body["passed_count"] == 2
    assert body["score"] == 100
    assert body["execution_time_ms"] == 18
    assert body["memory_kb"] == 4100
    assert body["ai_review"]["time_complexity"] == "O(1)"
    assert body["ai_review"]["space_complexity"] == "O(1)"
    public = next(item for item in body["results"] if not item["is_hidden"])
    hidden = next(item for item in body["results"] if item["is_hidden"])
    assert public["passed"] is True
    assert public["expected_stdout"] == "5\n"
    assert hidden["passed"] is True
    assert "expected_stdout" not in hidden
    assert "10 20" not in text
    assert "30\\n" not in text
    dumped = json.dumps(seen["payload"])
    assert "10 20" not in dumped
    assert "30\\n" not in dumped
    summary = client.get("/api/v1/dashboard/summary", headers=auth_header(token))
    assert summary.get_json()["coding_score"] == 100


def test_failed_and_empty_runs_are_stored(client, app):
    token, _student_id = register(client, email="code.fail@example.com", roll_number="CS503")
    problem = sum_problem(client, token)
    app.extensions["code_runner"] = passing_runner
    app.extensions["llm"] = lambda _instructions, _payload: REVIEW
    failed = client.post(
        f"/api/v1/coding/problems/{problem['id']}/submit",
        headers=auth_header(token),
        json={"language": "python", "source_code": "print(0)\n"},
    )
    assert failed.status_code == 201
    assert failed.get_json()["status"] == "wrong_answer"
    assert failed.get_json()["score"] == 0
    assert "30\\n" not in failed.get_data(as_text=True)
    broken = client.post(
        f"/api/v1/coding/problems/{problem['id']}/submit",
        headers=auth_header(token),
        json={"language": "java", "source_code": "compile-me"},
    )
    assert broken.status_code == 201
    assert broken.get_json()["status"] == "compilation_error"
    assert "expected ';'" in broken.get_data(as_text=True)

    # A runner that produces no output (for example a missing toolchain) still
    # stores a graded submission. A stub keeps the test independent of whether
    # javac is installed or how fast this machine starts a JVM.
    app.extensions["code_runner"] = lambda *_args: {
        "status": "accepted",
        "stdout": "",
        "stderr": "",
        "time_ms": None,
        "memory_kb": None,
    }
    with app.app_context():
        before = db.session.scalar(select(func.count()).select_from(CodingSubmission))
    missing = client.post(
        f"/api/v1/coding/problems/{problem['id']}/submit",
        headers=auth_header(token),
        json={"language": "java", "source_code": "class Main { public static void main(String[] args) {} }"},
    )
    assert missing.status_code == 201
    assert missing.get_json()["status"] == "wrong_answer"
    with app.app_context():
        after = db.session.scalar(select(func.count()).select_from(CodingSubmission))
    assert after == before + 1


def test_review_failure_keeps_the_execution(client, app):
    token, _student_id = register(client, email="code.review@example.com", roll_number="CS504")
    problem = sum_problem(client, token)
    app.extensions["code_runner"] = passing_runner

    def unavailable(_instructions, _payload):
        raise ApiError(503, "llm_not_configured", "Set LLM_PROVIDER before a review can run.")

    app.extensions["llm"] = unavailable
    response = client.post(
        f"/api/v1/coding/problems/{problem['id']}/submit",
        headers=auth_header(token),
        json={"language": "python", "source_code": problem["starter_code"]["python"]},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "accepted"
    assert body["ai_review"] is None
    assert "Set LLM_PROVIDER" in body["review_error"]


def test_tpo_cannot_open_coding_or_companies(client):
    registered = register_tpo(client, email="office.code@example.com")
    token = registered.get_json()["access_token"]
    coding = client.get("/api/v1/coding/problems", headers=auth_header(token))
    companies = client.get("/api/v1/companies", headers=auth_header(token))
    assert coding.status_code == 403
    assert companies.status_code == 403


def test_company_questions_keep_curated_and_ai_sources_separate(client, app):
    token, _student_id = register(client, email="company.prep@example.com", roll_number="CS505")
    listed = client.get("/api/v1/companies", headers=auth_header(token))
    assert listed.status_code == 200
    slugs = {item["slug"] for item in listed.get_json()["items"]}
    assert {"amazon", "tcs", "infosys"} <= slugs

    curated = client.get(
        "/api/v1/companies/tcs/questions?category=hr&difficulty=beginner&source=curated",
        headers=auth_header(token),
    )
    assert curated.status_code == 200
    curated_items = curated.get_json()["items"]
    assert curated_items
    assert {item["source"] for item in curated_items} == {"curated"}
    assert all(item["difficulty"] == "beginner" for item in curated_items)
    assert all(item["preparation_tip"] for item in curated_items)

    def generated(_instructions, _payload):
        return {
            "questions": [
                {
                    "topic": "Projects",
                    "prompt": "Which tradeoff did you reject while building your campus project?",
                    "preparation_tip": "Name the option you rejected and the reason.",
                }
            ]
        }

    app.extensions["llm"] = generated
    created = client.post(
        "/api/v1/companies/tcs/practice-questions",
        headers=auth_header(token),
        json={"category": "technical", "difficulty": "intermediate", "count": 1},
    )
    assert created.status_code == 201
    assert created.get_json()["items"][0]["source"] == "ai_generated"

    still_curated = client.get(
        "/api/v1/companies/tcs/questions?source=curated",
        headers=auth_header(token),
    )
    prompts = [item["prompt"] for item in still_curated.get_json()["items"]]
    assert "Which tradeoff did you reject while building your campus project?" not in prompts
    generated_only = client.get(
        "/api/v1/companies/tcs/questions?source=ai_generated&difficulty=intermediate",
        headers=auth_header(token),
    )
    assert generated_only.get_json()["items"][0]["source"] == "ai_generated"


def test_communication_without_speech_credentials_stores_nothing(client, app):
    token, _student_id = register(client, email="speech.missing@example.com", roll_number="CS506")
    response = client.post(
        "/api/v1/communication/analyses",
        headers=auth_header(token),
        data={"audio": (BytesIO(b"RIFFfake"), "answer.wav"), "duration_seconds": "12"},
    )
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "speech_not_configured"
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(CommunicationAnalysis)) == 0


def test_communication_scores_pace_and_fillers_from_the_transcript(client, app):
    token, student_id = register(client, email="speech.ok@example.com", roll_number="CS507")
    with app.app_context():
        user = db.session.get(User, uuid.UUID(student_id))
        session = InterviewSession(student_id=user.id, kind="hr", status="completed")
        db.session.add(session)
        db.session.flush()
        turn = InterviewTurn(session_id=session.id, turn_index=1, question_text="Describe your project.")
        db.session.add(turn)
        db.session.commit()
        session_id = str(session.id)
        turn_id = str(turn.id)

    app.extensions["transcriber"] = lambda content, mime: TRANSCRIPT if content and mime else ""
    app.extensions["llm"] = lambda _instructions, _payload: {
        "clarity_feedback": "Replace the filler with the feature you built, then name the database table."
    }
    response = client.post(
        "/api/v1/communication/analyses",
        headers=auth_header(token),
        data={
            "audio": (BytesIO(b"not-a-real-codec-but-stored"), "answer.webm"),
            "duration_seconds": "12",
            "session_id": session_id,
            "turn_id": turn_id,
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    fillers = count_fillers(TRANSCRIPT)
    words = len(re.findall(r"[A-Za-z0-9']+", TRANSCRIPT))
    wpm = round(words / (12 / 60), 1)
    assert body["transcript"] == TRANSCRIPT
    assert body["words_per_minute"] == wpm
    assert body["filler_count"] == fillers["count"]
    assert body["filler_words"]["um"] == 1
    assert body["communication_score"] == communication_score(wpm, fillers["count"], words)
    assert body["pause_count"] is None
    assert body["session_id"] == session_id
    assert "filler" in body["clarity_feedback"]
    with app.app_context():
        row = db.session.get(CommunicationAnalysis, uuid.UUID(body["id"]))
        assert row is not None
        assert Path(row.audio_path).is_file()
    summary = client.get("/api/v1/dashboard/summary", headers=auth_header(token))
    assert summary.get_json()["communication_score"] == body["communication_score"]

    denied = client.post(
        "/api/v1/communication/analyses",
        headers=auth_header(register_tpo(client, email="office.speech@example.com").get_json()["access_token"]),
        data={"audio": (BytesIO(b"abc"), "answer.wav"), "duration_seconds": "8"},
    )
    assert denied.status_code == 403

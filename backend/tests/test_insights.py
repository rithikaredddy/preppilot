from uuid import UUID

from app.extensions import db
from app.services import scoring
from tests.test_auth import auth_header, register_tpo
from tests.test_catalog import register, sum_problem


def seed_scores(app, user_id: str) -> None:
    student_id = UUID(user_id)
    with app.app_context():
        scoring.record_score(student_id, "resume", 68, "resume_analysis", student_id, [], ["SQL"])
        scoring.record_score(student_id, "hr", 74, "interview_session", student_id, [], [])
        scoring.record_score(student_id, "technical", 70, "interview_session", student_id, [], [])
        scoring.record_score(student_id, "coding", 46, "coding_submission", student_id, [], ["edge cases"])
        scoring.record_score(student_id, "communication", 71, "interview_session", student_id, [], [])
        db.session.commit()


def test_readiness_stores_a_trend_and_what_if_moves(client, app):
    token, user_id = register(client)
    empty = client.get("/api/v1/readiness", headers=auth_header(token))
    assert empty.status_code == 200
    assert empty.get_json()["current"] is None

    seed_scores(app, user_id)
    saved = client.get("/api/v1/readiness", headers=auth_header(token))
    assert saved.status_code == 200
    body = saved.get_json()
    assert body["current"]["readiness_percentage"] > 0
    assert "biggest factor" in body["current"]["headline"]
    assert body["history"]

    base = {
        "resume_ats": 68,
        "interview_score": 72,
        "coding_score": 46,
        "communication_score": 71,
    }
    low = client.post("/api/v1/readiness/what-if", json=base, headers=auth_header(token))
    high = client.post(
        "/api/v1/readiness/what-if",
        json={**base, "coding_score": 90},
        headers=auth_header(token),
    )
    assert low.status_code == 200
    assert high.status_code == 200
    assert high.get_json()["readiness_percentage"] > low.get_json()["readiness_percentage"]

    officer = register_tpo(client).get_json()
    blocked = client.get("/api/v1/readiness", headers=auth_header(officer["access_token"]))
    assert blocked.status_code == 403


def test_roadmap_completion_shrinks_the_gap(client, app):
    token, user_id = register(client)
    seed_scores(app, user_id)
    created = client.post("/api/v1/roadmap", headers=auth_header(token))
    assert created.status_code == 201
    payload = created.get_json()
    assert payload["items"]
    assert payload["note"]
    before = payload["gap"]["remaining_gap"]
    item_id = payload["items"][0]["id"]
    updated = client.patch(
        f"/api/v1/roadmap/{item_id}",
        json={"is_complete": True},
        headers=auth_header(token),
    )
    assert updated.status_code == 200
    assert updated.get_json()["is_complete"] is True
    analytics = client.get("/api/v1/dashboard/analytics", headers=auth_header(token))
    assert analytics.status_code == 200
    assert analytics.get_json()["gap"]["remaining_gap"] < before
    assert analytics.get_json()["weak_areas"]


def test_tpo_sees_readiness_without_transcripts(client, app):
    token, user_id = register(client)
    seed_scores(app, user_id)
    client.get("/api/v1/readiness", headers=auth_header(token))
    officer = register_tpo(client).get_json()
    headers = auth_header(officer["access_token"])
    listing = client.get("/api/v1/tpo/students?readiness_below=100&sort=readiness", headers=headers)
    assert listing.status_code == 200
    item = listing.get_json()["items"][0]
    assert item["readiness_percentage"] is not None
    detail = client.get(f"/api/v1/tpo/students/{user_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.get_json()
    assert body["scores"]
    serialized = detail.get_data(as_text=True)
    assert "transcript" not in serialized
    assert "answer_text" not in serialized
    student_blocked = client.get("/api/v1/tpo/insights", headers=auth_header(token))
    assert student_blocked.status_code == 403


def test_performance_pdf_and_python_sandbox(client, app):
    token, user_id = register(client)
    missing = client.get("/api/v1/reports/performance", headers=auth_header(token))
    assert missing.status_code == 422
    seed_scores(app, user_id)
    report = client.get("/api/v1/reports/performance", headers=auth_header(token))
    assert report.status_code == 200
    assert report.data.startswith(b"%PDF")

    problem = sum_problem(client, token)
    ran = client.post(
        f"/api/v1/coding/problems/{problem['id']}/run",
        json={
            "language": "python",
            "source_code": "a, b = map(int, input().split())\nprint(a + b)\n",
        },
        headers=auth_header(token),
    )
    assert ran.status_code == 200
    assert ran.get_json()["passed_count"] == 1
    problems = client.get("/api/v1/coding/problems", headers=auth_header(token))
    assert len(problems.get_json()["items"]) >= 15


def test_sandbox_blocks_network(client):
    token, _user_id = register(client, email="net@example.com", roll_number="CS009")
    problem = sum_problem(client, token)
    ran = client.post(
        f"/api/v1/coding/problems/{problem['id']}/run",
        json={
            "language": "python",
            "source_code": "import socket\nprint(socket.create_connection(('example.com', 80)))\n",
        },
        headers=auth_header(token),
    )
    assert ran.status_code == 200
    body = ran.get_json()
    assert body["passed_count"] == 0
    assert "Network access is disabled" in body["results"][0]["stderr"]

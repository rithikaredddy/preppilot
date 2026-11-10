from sqlalchemy import select

from app.extensions import db
from app.models import User
from app.services.auth_service import verify_password


def student_payload(**overrides):
    payload = {
        "email": "ada@example.com",
        "password": "Password1",
        "role": "student",
        "full_name": "Ada Lovelace",
        "roll_number": "CS001",
        "branch": "CSE",
        "graduation_year": 2026,
    }
    payload.update(overrides)
    return payload


def tpo_payload(**overrides):
    payload = {
        "email": "office@example.com",
        "password": "Password1",
        "role": "tpo",
        "full_name": "Placement Officer",
        "department": "Training and Placement",
        "designation": "TPO",
        "otp": "000000",
    }
    payload.update(overrides)
    return payload


def register_tpo(client, **overrides):
    payload = tpo_payload(**overrides)
    requested = client.post("/api/v1/auth/tpo-otp", json={"email": payload["email"]})
    payload["otp"] = requested.get_json()["otp"]
    return client.post("/api/v1/auth/register", json=payload)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.get_json()["database"] == "ok"


def test_register_student_persists_hashed_password(client, app):
    response = client.post("/api/v1/auth/register", json=student_payload())
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["role"] == "student"
    assert body["user"]["roll_number"] == "CS001"
    assert "password" not in body["user"]

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.password_hash != "Password1"
        assert user.password_hash.startswith("$2")
        assert verify_password("Password1", user.password_hash)
        assert user.student_profile.branch == "CSE"


def test_duplicate_email_and_roll_number(client):
    assert client.post("/api/v1/auth/register", json=student_payload()).status_code == 201
    duplicate_email = client.post(
        "/api/v1/auth/register",
        json=student_payload(roll_number="CS002"),
    )
    assert duplicate_email.status_code == 409
    duplicate_roll = client.post(
        "/api/v1/auth/register",
        json=student_payload(email="other@example.com", roll_number="cs001"),
    )
    assert duplicate_roll.status_code == 409


def test_student_registration_requires_roll_number(client):
    payload = student_payload()
    del payload["roll_number"]
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "roll_number" in response.get_json()["error"]["details"]


def test_weak_password_is_rejected(client):
    response = client.post("/api/v1/auth/register", json=student_payload(password="password"))
    assert response.status_code == 422


def test_tpo_registration_requires_emailed_otp(client):
    missing = client.post("/api/v1/auth/register", json=tpo_payload(otp="123456"))
    assert missing.status_code == 400

    requested = client.post("/api/v1/auth/tpo-otp", json={"email": "office@example.com"})
    assert requested.status_code == 200
    code = requested.get_json()["otp"]
    rejected = client.post("/api/v1/auth/register", json=tpo_payload(otp="000000"))
    assert rejected.status_code == 400
    created = client.post("/api/v1/auth/register", json=tpo_payload(otp=code))
    assert created.status_code == 201
    assert created.get_json()["user"]["role"] == "tpo"
    assert created.get_json()["user"]["department"] == "Training and Placement"
    reused = client.post(
        "/api/v1/auth/register",
        json=tpo_payload(email="second.office@example.com", otp=code),
    )
    assert reused.status_code == 400


def test_login_and_me(client):
    client.post("/api/v1/auth/register", json=student_payload())
    rejected = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "wrongpass1"},
    )
    assert rejected.status_code == 401
    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401

    signed_in = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "Password1"},
    )
    assert signed_in.status_code == 200
    token = signed_in.get_json()["access_token"]
    me = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.get_json()["email"] == "ada@example.com"


def test_role_permissions(client):
    student = client.post("/api/v1/auth/register", json=student_payload()).get_json()
    officer = register_tpo(client).get_json()

    student_on_tpo = client.get(
        "/api/v1/tpo/students", headers=auth_header(student["access_token"])
    )
    assert student_on_tpo.status_code == 403

    officer_on_dashboard = client.get(
        "/api/v1/dashboard/summary",
        headers=auth_header(officer["access_token"]),
    )
    assert officer_on_dashboard.status_code == 403

    listing = client.get("/api/v1/tpo/students", headers=auth_header(officer["access_token"]))
    assert listing.status_code == 200
    body = listing.get_json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "ada@example.com"
    serialized = listing.get_data(as_text=True)
    assert "password_hash" not in serialized
    assert "Password1" not in serialized

    summary = client.get("/api/v1/dashboard/summary", headers=auth_header(student["access_token"]))
    assert summary.status_code == 200
    assert summary.get_json()["resume_score"] is None
    assert summary.get_json()["completed_sessions"] == 0


def test_branch_filter_and_sort(client):
    client.post("/api/v1/auth/register", json=student_payload())
    client.post(
        "/api/v1/auth/register",
        json=student_payload(
            email="grace@example.com", roll_number="IT002", full_name="Grace Hopper", branch="IT"
        ),
    )
    officer = register_tpo(client).get_json()
    filtered = client.get(
        "/api/v1/tpo/students?branch=it&sort=roll_number",
        headers=auth_header(officer["access_token"]),
    )
    assert filtered.status_code == 200
    items = filtered.get_json()["items"]
    assert len(items) == 1
    assert items[0]["roll_number"] == "IT002"


def test_logout_revokes_refresh_token(client):
    registered = client.post("/api/v1/auth/register", json=student_payload()).get_json()
    logged_out = client.post(
        "/api/v1/auth/logout", json={"refresh_token": registered["refresh_token"]}
    )
    assert logged_out.status_code == 200
    refreshed = client.post(
        "/api/v1/auth/refresh", headers=auth_header(registered["refresh_token"])
    )
    assert refreshed.status_code == 401


def test_refresh_rotates_token(client):
    registered = client.post("/api/v1/auth/register", json=student_payload()).get_json()
    refreshed = client.post(
        "/api/v1/auth/refresh", headers=auth_header(registered["refresh_token"])
    )
    assert refreshed.status_code == 200
    new_refresh = refreshed.get_json()["refresh_token"]
    assert new_refresh != registered["refresh_token"]
    old_again = client.post(
        "/api/v1/auth/refresh", headers=auth_header(registered["refresh_token"])
    )
    assert old_again.status_code == 401
    me = client.get("/api/v1/auth/me", headers=auth_header(refreshed.get_json()["access_token"]))
    assert me.status_code == 200


def test_password_reset_flow(client):
    client.post("/api/v1/auth/register", json=student_payload())
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})
    assert unknown.status_code == 200
    assert "reset_token" not in unknown.get_json()

    requested = client.post("/api/v1/auth/forgot-password", json={"email": "ada@example.com"})
    assert requested.status_code == 200
    token = requested.get_json()["reset_token"]
    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "NewPassword2"},
    )
    assert reset.status_code == 200
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "Password1"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "NewPassword2"},
    )
    assert new_login.status_code == 200
    reused = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "AnotherPass3"},
    )
    assert reused.status_code == 400


def test_profile_update_persists_and_blocks_other_role_fields(client, app):
    registered = client.post("/api/v1/auth/register", json=student_payload()).get_json()
    headers = auth_header(registered["access_token"])
    rejected = client.patch("/api/v1/profile", json={"department": "Placement"}, headers=headers)
    assert rejected.status_code == 422

    updated = client.patch(
        "/api/v1/profile",
        json={"branch": "CSE - Data Science", "cgpa": 8.5, "phone": "9876543210"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.get_json()["branch"] == "CSE - Data Science"
    assert updated.get_json()["cgpa"] == 8.5

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user.student_profile.branch == "CSE - Data Science"
        assert float(user.student_profile.cgpa) == 8.5

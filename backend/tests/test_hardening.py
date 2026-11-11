"""Security and deployment safeguards added after the project audit."""

import pytest

from app.config import ROOT_DIR, _check_production, _normalize_database_url, _resolve_path
from app.services.sandbox import run_local
from tests.test_auth import auth_header, student_payload

ENV_FILE = str(ROOT_DIR / ".env")


def run(source: str, stdin: str = "") -> dict:
    return run_local(source, "python", stdin, 2000, 128000)


@pytest.mark.parametrize(
    "source",
    [
        f"print(open({ENV_FILE!r}).read())",
        f"import io; print(io.FileIO({ENV_FILE!r}).read())",
        "import subprocess; subprocess.run(['whoami'])",
        "import os; os.system('whoami')",
        "import posix; posix.system('whoami')",
        "import socket; socket.create_connection(('example.com', 80))",
        "open('/tmp/sandbox-escape.txt', 'w').write('x')",
        "import os; print(os.listdir('/'))",
    ],
)
def test_sandbox_blocks_escapes(source):
    result = run(source)
    assert result["status"] == "runtime_error"
    assert "Error" in result["stderr"]


def test_sandbox_hides_server_secrets():
    result = run("import os; print(sorted(k for k in os.environ if 'SECRET' in k or 'KEY' in k))")
    assert result["status"] == "accepted"
    assert result["stdout"].strip() == "[]"


@pytest.mark.parametrize(
    ("source", "stdin", "expected"),
    [
        ("a, b = map(int, input().split()); print(a + b)", "2 3\n", "5"),
        ("print(sum(map(int, open(0).read().split())))", "2 3\n", "5"),
        ("import re, json, heapq, bisect, random, collections; print('ok')", "", "ok"),
        ("open('scratch.txt', 'w').write('hi'); print(open('scratch.txt').read())", "", "hi"),
    ],
)
def test_sandbox_still_runs_normal_programs(source, stdin, expected):
    result = run(source, stdin)
    assert result["status"] == "accepted", result["stderr"]
    assert result["stdout"].strip() == expected


def test_sandbox_stops_infinite_loops():
    assert run("while True: pass")["status"] == "time_limit"


def test_local_runner_can_be_disabled(client, app):
    payload = student_payload(email="runner.off@example.com", roll_number="CS900")
    token = client.post("/api/v1/auth/register", json=payload).get_json()["access_token"]
    problems = client.get("/api/v1/coding/problems", headers=auth_header(token)).get_json()["items"]
    app.config["ALLOW_LOCAL_CODE_RUNNER"] = False
    try:
        response = client.post(
            f"/api/v1/coding/problems/{problems[0]['id']}/run",
            headers=auth_header(token),
            json={"language": "python", "source_code": "print(1)"},
        )
    finally:
        app.config["ALLOW_LOCAL_CODE_RUNNER"] = True
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "code_runner_not_configured"


def test_repeated_failed_logins_are_throttled(client, app):
    payload = student_payload(email="throttle@example.com", roll_number="CS901")
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    wrong = {"email": payload["email"], "password": "WrongPassword123!"}
    for _ in range(app.config["LOGIN_MAX_FAILURES"]):
        assert client.post("/api/v1/auth/login", json=wrong).status_code == 401
    blocked = client.post("/api/v1/auth/login", json=wrong)
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "too_many_attempts"
    correct = {"email": payload["email"], "password": payload["password"]}
    assert client.post("/api/v1/auth/login", json=correct).status_code == 429


def test_successful_login_clears_failures(client):
    payload = student_payload(email="recover@example.com", roll_number="CS902")
    client.post("/api/v1/auth/register", json=payload)
    wrong = {"email": payload["email"], "password": "WrongPassword123!"}
    for _ in range(3):
        client.post("/api/v1/auth/login", json=wrong)
    correct = {"email": payload["email"], "password": payload["password"]}
    assert client.post("/api/v1/auth/login", json=correct).status_code == 200
    for _ in range(3):
        assert client.post("/api/v1/auth/login", json=wrong).status_code == 401


def test_production_rejects_unsafe_settings():
    with pytest.raises(RuntimeError) as error:
        _check_production(
            jwt_secret="dev-only-change-me",
            secret_key="short",
            expose_reset=True,
            tpo_allowed_emails=[],
        )
    message = str(error.value)
    for name in ("JWT_SECRET", "SECRET_KEY", "PASSWORD_RESET_DEV_EXPOSE", "TPO_ALLOWED_EMAILS"):
        assert name in message


def test_production_accepts_safe_settings():
    _check_production(
        jwt_secret="a" * 64,
        secret_key="b" * 64,
        expose_reset=False,
        tpo_allowed_emails=["tpo@college.edu"],
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgres://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ],
)
def test_database_url_gets_a_driver(url, expected):
    assert _normalize_database_url(url) == expected


def test_relative_upload_dir_resolves_from_project_root():
    assert _resolve_path("backend/uploads") == str((ROOT_DIR / "backend" / "uploads").resolve())
    assert _resolve_path("/var/data/uploads") == "/var/data/uploads"


def test_local_runner_can_be_limited_to_python(client, app):
    payload = student_payload(email="python.only@example.com", roll_number="CS903")
    token = client.post("/api/v1/auth/register", json=payload).get_json()["access_token"]
    problems = client.get("/api/v1/coding/problems", headers=auth_header(token)).get_json()["items"]
    app.config["LOCAL_RUNNER_LANGUAGES"] = ["python"]
    try:
        response = client.post(
            f"/api/v1/coding/problems/{problems[0]['id']}/run",
            headers=auth_header(token),
            json={"language": "java", "source_code": "class Main {}"},
        )
    finally:
        app.config["LOCAL_RUNNER_LANGUAGES"] = ["python", "java", "cpp"]
    assert response.status_code == 503
    assert "Java is not available" in response.get_json()["error"]["message"]

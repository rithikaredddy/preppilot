import os
import tempfile
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[2]


def load_settings(*, testing: bool) -> dict:
    if not testing:
        load_dotenv(ROOT_DIR / ".env")

    if testing:
        database_url = "sqlite://"
        engine_options = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
        jwt_secret = "test-jwt-secret-with-32-byte-length"
        secret_key = "test-secret-with-32-byte-length"
        tpo_allowed_emails: list[str] = []
        expose_reset = True
        env_name = "testing"
        cors_origins = ["http://localhost:5173"]
        upload_dir = tempfile.mkdtemp(prefix="interview-test-uploads-")
        llm_provider = "openai"
        openai_key = ""
        gemini_key = ""
        anthropic_key = ""
        judge0_url = ""
        judge0_key = ""
        judge0_host = ""
        allow_local_code = True
        local_languages = ["python", "java", "cpp"]
    else:
        database_url = _normalize_database_url(
            os.environ.get(
                "DATABASE_URL",
                "postgresql+psycopg://interview:interview@localhost:5433/interview_prep",
            )
        )
        engine_options = {}
        jwt_secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
        secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
        tpo_allowed_emails = [
            email.strip().lower()
            for email in os.environ.get("TPO_ALLOWED_EMAILS", "").split(",")
            if email.strip()
        ]
        expose_reset = os.environ.get("PASSWORD_RESET_DEV_EXPOSE", "false").lower() == "true"
        env_name = os.environ.get("ENV_NAME", "development")
        cors_origins = [
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]
        upload_dir = _resolve_path(os.environ.get("UPLOAD_DIR", "backend/uploads"))
        llm_provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        judge0_url = os.environ.get("JUDGE0_URL", "").rstrip("/")
        judge0_key = os.environ.get("JUDGE0_API_KEY", "")
        judge0_host = os.environ.get("JUDGE0_HOST", "")
        allow_local_code = _flag("ALLOW_LOCAL_CODE_RUNNER", default=env_name != "production")
        # Python has an in-process guard; Java and C++ only get a clean environment,
        # so a public server should list just "python" here and use Judge0 for the rest.
        local_languages = [
            item.strip().lower()
            for item in os.environ.get("LOCAL_RUNNER_LANGUAGES", "python,java,cpp").split(",")
            if item.strip()
        ]
        if env_name == "production":
            _check_production(
                jwt_secret=jwt_secret,
                secret_key=secret_key,
                expose_reset=expose_reset,
                tpo_allowed_emails=tpo_allowed_emails,
            )

    return {
        "ENV_NAME": env_name,
        "SECRET_KEY": secret_key,
        "JWT_SECRET_KEY": jwt_secret,
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(
            minutes=int(os.environ.get("JWT_ACCESS_MINUTES", "30"))
        ),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", "7"))),
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": engine_options,
        "TPO_ALLOWED_EMAILS": tpo_allowed_emails,
        "PASSWORD_RESET_DEV_EXPOSE": expose_reset,
        "FRONTEND_URL": os.environ.get("FRONTEND_URL", "http://localhost:5173"),
        "CORS_ORIGINS": cors_origins,
        "SMTP_HOST": os.environ.get("SMTP_HOST", ""),
        "SMTP_PORT": int(os.environ.get("SMTP_PORT", "587")),
        "SMTP_USERNAME": os.environ.get("SMTP_USERNAME", ""),
        "SMTP_PASSWORD": os.environ.get("SMTP_PASSWORD", ""),
        "SMTP_FROM": os.environ.get("SMTP_FROM", ""),
        "UPLOAD_DIR": upload_dir,
        "MAX_UPLOAD_BYTES": int(os.environ.get("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
        "LLM_PROVIDER": llm_provider,
        "OPENAI_API_KEY": openai_key,
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "GEMINI_API_KEY": gemini_key,
        "ANTHROPIC_API_KEY": anthropic_key,
        "ANTHROPIC_MODEL": os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5"),
        "ANTHROPIC_EFFORT": os.environ.get("ANTHROPIC_EFFORT", "low"),
        "GEMINI_MODEL": os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        "JUDGE0_URL": judge0_url,
        "JUDGE0_API_KEY": judge0_key,
        "JUDGE0_HOST": judge0_host,
        "ALLOW_LOCAL_CODE_RUNNER": allow_local_code,
        "LOCAL_RUNNER_LANGUAGES": local_languages,
        "LOGIN_MAX_FAILURES": int(os.environ.get("LOGIN_MAX_FAILURES", "5")),
        "LOGIN_LOCKOUT_MINUTES": int(os.environ.get("LOGIN_LOCKOUT_MINUTES", "15")),
        "API_TITLE": "AI Interview Preparation Platform",
        "API_VERSION": "v1",
        "OPENAPI_VERSION": "3.0.3",
        "OPENAPI_URL_PREFIX": "/api/v1",
        "OPENAPI_SWAGGER_UI_PATH": "/docs",
        "OPENAPI_SWAGGER_UI_URL": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
        "API_SPEC_OPTIONS": {
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
                }
            }
        },
    }


_PLACEHOLDER_SECRETS = {"", "dev-only-change-me", "replace-with-a-long-random-string"}


def _flag(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_path(value: str) -> str:
    """Resolve a relative path against the project root, not the shell's folder."""
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else (ROOT_DIR / path).resolve())


def _normalize_database_url(url: str) -> str:
    """Hosted Postgres providers hand out postgres:// URLs; SQLAlchemy needs a driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _check_production(
    *, jwt_secret: str, secret_key: str, expose_reset: bool, tpo_allowed_emails: list[str]
) -> None:
    problems = []
    if jwt_secret in _PLACEHOLDER_SECRETS or len(jwt_secret) < 32:
        problems.append("JWT_SECRET must be a random string of at least 32 characters")
    if secret_key in _PLACEHOLDER_SECRETS or len(secret_key) < 32:
        problems.append("SECRET_KEY must be a random string of at least 32 characters")
    if expose_reset:
        problems.append("PASSWORD_RESET_DEV_EXPOSE must be false")
    if not tpo_allowed_emails:
        problems.append("TPO_ALLOWED_EMAILS must list the placement office addresses")
    if problems:
        raise RuntimeError("Production settings are unsafe: " + "; ".join(problems) + ".")

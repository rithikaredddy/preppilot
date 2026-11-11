import logging

import httpx
from flask import current_app

from app.errors import ApiError

logger = logging.getLogger(__name__)

LANGUAGE_IDS = {"python": 71, "java": 62, "cpp": 54}
STATUS_NAMES = {
    3: "accepted",
    4: "wrong_answer",
    5: "time_limit",
    6: "compilation_error",
    7: "runtime_error",
    8: "runtime_error",
    9: "runtime_error",
    10: "runtime_error",
    11: "runtime_error",
    12: "runtime_error",
    13: "error",
    14: "error",
}


def execute(source_code: str, language: str, stdin: str, time_limit_ms: int, memory_limit_kb: int) -> dict:
    """Run one program in Judge0, or locally when Judge0 is unset.

    Tests may set ``app.extensions["code_runner"]``. Python, Java, and C++
    each run in a timed subprocess when no Judge0 URL is configured.
    """
    override = current_app.extensions.get("code_runner")
    if override is not None:
        return override(source_code, language, stdin, time_limit_ms, memory_limit_kb)
    url = current_app.config["JUDGE0_URL"].strip()
    if not url:
        if not current_app.config.get("ALLOW_LOCAL_CODE_RUNNER", False):
            raise ApiError(
                503,
                "code_runner_not_configured",
                "Code execution needs JUDGE0_URL on this server.",
            )
        if language in {"python", "java", "cpp"}:
            if language not in current_app.config.get("LOCAL_RUNNER_LANGUAGES", []):
                names = {"python": "Python", "java": "Java", "cpp": "C++"}
                raise ApiError(
                    503,
                    "code_runner_not_configured",
                    f"{names[language]} is not available on this server yet. Try Python, "
                    "or ask the administrator to set JUDGE0_URL.",
                )
            from app.services.sandbox import run_local

            return run_local(source_code, language, stdin, time_limit_ms, memory_limit_kb)
        raise ApiError(422, "validation_error", "Choose Python, Java, or C++.")
    language_id = LANGUAGE_IDS.get(language)
    if language_id is None:
        raise ApiError(422, "validation_error", "Choose Python, Java, or C++.")
    headers = {}
    api_key = current_app.config["JUDGE0_API_KEY"].strip()
    host = current_app.config["JUDGE0_HOST"].strip()
    if api_key:
        headers["X-RapidAPI-Key"] = api_key
        if host:
            headers["X-RapidAPI-Host"] = host
    body = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
        "cpu_time_limit": max(time_limit_ms / 1000, 1),
        "memory_limit": memory_limit_kb,
    }
    try:
        response = httpx.post(
            f"{url}/submissions",
            params={"base64_encoded": "false", "wait": "true"},
            headers=headers,
            json=body,
            timeout=httpx.Timeout(30.0),
        )
    except httpx.HTTPError as exc:
        logger.warning("judge0 unreachable: %s", exc)
        raise ApiError(502, "code_runner_error", "The code sandbox could not be reached.") from exc
    if response.status_code >= 400:
        logger.warning("judge0 status %s", response.status_code)
        raise ApiError(502, "code_runner_error", "The code sandbox rejected the program.")
    payload = response.json()
    status_id = (payload.get("status") or {}).get("id")
    return {
        "status": STATUS_NAMES.get(status_id, "error"),
        "stdout": payload.get("stdout") or "",
        "stderr": payload.get("stderr") or payload.get("compile_output") or "",
        "time_ms": _millis(payload.get("time")),
        "memory_kb": payload.get("memory"),
    }


def _millis(value) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value) * 1000)

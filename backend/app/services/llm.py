import json
import logging
import re
import time

import anthropic
import httpx
from flask import current_app

from app.errors import ApiError

logger = logging.getLogger(__name__)


class LLMResponseError(ApiError):
    def __init__(self, message: str):
        super().__init__(502, "llm_response_invalid", message)


def complete_json(instructions: str, payload: dict) -> tuple[dict, str, str]:
    """Call the configured model and return parsed JSON, provider, and model name.

    A missing API key raises 503 and does not invent a result. Tests may set
    ``app.extensions["llm"]`` to a callable. The running app does not set it.
    """
    started = time.perf_counter()
    override = current_app.extensions.get("llm")
    if override is not None:
        data = override(instructions, payload)
        provider = current_app.config["LLM_PROVIDER"]
        model = _configured_model(provider)
        parsed = _as_object(data)
    else:
        provider = current_app.config["LLM_PROVIDER"]
        if provider == "openai":
            parsed, model = _openai(instructions, payload)
        elif provider == "gemini":
            parsed, model = _gemini(instructions, payload)
        elif provider == "anthropic":
            parsed, model = _anthropic(instructions, payload)
        else:
            raise ApiError(
                503,
                "llm_not_configured",
                "Set LLM_PROVIDER to anthropic, openai or gemini, and add the matching API key.",
            )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info("llm provider=%s model=%s elapsed_ms=%s", provider, model, elapsed_ms)
    return parsed, provider, model


def require_text(data: dict, key: str, *, max_length: int = 2000) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LLMResponseError(f"The model response is missing {key}.")
    return value.strip()[:max_length]


def require_string_list(
    data: dict, key: str, *, min_items: int = 0, max_items: int = 12
) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list):
        raise LLMResponseError(f"The model response is missing {key}.")
    cleaned: list[str] = []
    for item in value:
        text = _item_text(item)
        if text:
            cleaned.append(text[:500])
    if len(cleaned) < min_items:
        raise LLMResponseError(f"The model response did not include enough {key}.")
    return cleaned[:max_items]


def require_score(data: dict, key: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LLMResponseError(f"The model response is missing a numeric {key} score.")
    score = float(value)
    if score < 0 or score > 100:
        raise LLMResponseError(f"The {key} score must be between 0 and 100.")
    return round(score, 2)


def _openai(instructions: str, payload: dict) -> tuple[dict, str]:
    api_key = current_app.config["OPENAI_API_KEY"].strip()
    model = current_app.config["OPENAI_MODEL"].strip()
    if not api_key or not model:
        raise ApiError(
            503,
            "llm_not_configured",
            "Set OPENAI_API_KEY before using the resume analyzer or interviews.",
        )
    body = {
        "model": model,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": _JSON_ONLY,
            },
            {"role": "user", "content": _prompt(instructions, payload)},
        ],
    }
    data = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        body,
    )
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("The model response could not be read.") from exc
    return _as_object(parse_json_object(content)), model


def _configured_model(provider: str) -> str:
    key = {"anthropic": "ANTHROPIC_MODEL", "gemini": "GEMINI_MODEL"}.get(provider, "OPENAI_MODEL")
    return current_app.config.get(key, "")


_JSON_ONLY = "Return one JSON object and nothing else. Do not wrap it in markdown."


def _anthropic(instructions: str, payload: dict) -> tuple[dict, str]:
    api_key = current_app.config["ANTHROPIC_API_KEY"].strip()
    model = current_app.config["ANTHROPIC_MODEL"].strip()
    if not api_key or not model:
        raise ApiError(
            503,
            "llm_not_configured",
            "Set ANTHROPIC_API_KEY before using the resume analyzer or interviews.",
        )
    client = anthropic.Anthropic(api_key=api_key, timeout=90.0, max_retries=2)
    try:
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=_JSON_ONLY,
            output_config={"effort": current_app.config["ANTHROPIC_EFFORT"]},
            # Re-run a safety-classifier decline on Anthropic's recommended fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": _prompt(instructions, payload)}],
        )
    except anthropic.AuthenticationError as exc:
        raise ApiError(
            502, "llm_provider_error", "The language model rejected the API key."
        ) from exc
    except anthropic.PermissionDeniedError as exc:
        raise ApiError(
            502, "llm_provider_error", "This API key cannot use the configured model."
        ) from exc
    except anthropic.BadRequestError as exc:
        if "credit balance" in str(exc).lower():
            raise ApiError(
                402,
                "llm_quota_exhausted",
                "This Anthropic account has no credits left. Add credits in the Claude Console.",
            ) from exc
        logger.warning("anthropic bad request: %s", exc)
        raise ApiError(
            502, "llm_provider_error", "The language model request failed. Try again."
        ) from exc
    except anthropic.APIStatusError as exc:
        logger.warning("anthropic status %s", exc.status_code)
        raise ApiError(
            502, "llm_provider_error", "The language model request failed. Try again."
        ) from exc
    except anthropic.APIConnectionError as exc:
        logger.warning("anthropic unreachable: %s", exc)
        raise ApiError(
            502, "llm_provider_error", "The language model request failed. Try again."
        ) from exc

    if response.stop_reason == "refusal":
        raise LLMResponseError("The model declined this request. Try rewording the input.")
    if response.stop_reason == "max_tokens":
        raise LLMResponseError("The model response was cut off. Try a shorter input.")
    text = "".join(block.text for block in response.content if block.type == "text")
    return _as_object(parse_json_object(text)), response.model


def _gemini(instructions: str, payload: dict) -> tuple[dict, str]:
    api_key = current_app.config["GEMINI_API_KEY"].strip()
    model = current_app.config["GEMINI_MODEL"].strip()
    if not api_key or not model:
        raise ApiError(
            503,
            "llm_not_configured",
            "Set GEMINI_API_KEY before using the resume analyzer or interviews.",
        )
    body = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(instructions, payload)}]}],
        "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
    }
    data = _post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"x-goog-api-key": api_key},
        body,
    )
    try:
        parts = data["candidates"][0]["content"]["parts"]
        content = "".join(
            part.get("text", "") for part in parts if not part.get("thought")
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("The model response could not be read.") from exc
    return _as_object(parse_json_object(content)), model


def _post_json(url: str, headers: dict, body: dict, params: dict | None = None) -> dict:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = httpx.post(
                url, headers=headers, params=params, json=body, timeout=httpx.Timeout(60.0)
            )
        except httpx.HTTPError as exc:
            last_error = exc
            time.sleep(0.4)
            continue
        if response.status_code in {401, 403}:
            raise ApiError(502, "llm_provider_error", "The language model rejected the API key.")
        if response.status_code == 429 and _quota_exhausted(response):
            raise ApiError(
                402,
                "llm_quota_exhausted",
                "This model account has no credits left. For a free option, use a Gemini API key instead.",
            )
        if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
            time.sleep(0.4)
            continue
        if response.status_code >= 400:
            logger.warning("llm provider status %s", response.status_code)
            raise ApiError(
                502, "llm_provider_error", "The language model request failed. Try again."
            )
        try:
            return response.json()
        except ValueError as exc:
            raise LLMResponseError("The model response was not JSON.") from exc
    logger.warning("llm provider unreachable: %s", last_error)
    raise ApiError(502, "llm_provider_error", "The language model request failed. Try again.")


def _quota_exhausted(response: httpx.Response) -> bool:
    try:
        error = response.json().get("error", {})
    except ValueError:
        return False
    code = str(error.get("code") or "")
    return error.get("type") == "insufficient_quota" or code in {
        "insufficient_quota",
        "credit_balance_exhausted",
    }


def parse_json_object(value) -> dict:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        raise LLMResponseError("The model response was not a JSON object.")
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMResponseError("The model response was not valid JSON.") from exc
    return _as_object(parsed)


def _as_object(value) -> dict:
    if not isinstance(value, dict):
        raise LLMResponseError("The model response was not a JSON object.")
    return value


def _prompt(instructions: str, payload: dict) -> str:
    return f"{instructions}\n\nInput:\n{json.dumps(payload, ensure_ascii=False)}"


def _item_text(item) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        parts = [str(value).strip() for value in item.values() if str(value).strip()]
        return " — ".join(parts)
    return ""

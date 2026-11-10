import base64
import re
import uuid
from decimal import Decimal
from pathlib import Path

import httpx
from flask import current_app

from app.errors import ApiError
from app.extensions import db
from app.models.catalog import CommunicationAnalysis
from app.models.practice import InterviewSession, InterviewTurn
from app.models.user import User
from app.services import scoring
from app.services.llm import LLMResponseError, complete_json, parse_json_object, require_text

AUDIO_TYPES = {
    ".webm": "audio/webm",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}
FILLER_PHRASES = ("you know", "i mean")
FILLER_WORDS = ("um", "uh", "er", "ah", "hmm", "like", "basically", "actually")
FEEDBACK_INSTRUCTIONS = """
Give communication feedback for a placement interview answer.
Use only the transcript. Do not claim anything about emotion, personality, or voice tone.
Return JSON: {"clarity_feedback": "two sentences of specific advice"}.
""".strip()


def analyze(
    student: User,
    upload,
    duration_seconds: float | None,
    session_id,
    turn_id,
) -> CommunicationAnalysis:
    if session_id is not None:
        session = db.session.get(InterviewSession, session_id)
        if session is None or session.student_id != student.id:
            raise ApiError(404, "not_found", "That interview was not found.")
    if turn_id is not None:
        turn = db.session.get(InterviewTurn, turn_id)
        if turn is None or turn.session.student_id != student.id:
            raise ApiError(404, "not_found", "That interview answer was not found.")
        if session_id is not None and turn.session_id != session_id:
            raise ApiError(422, "validation_error", "That answer does not belong to the selected interview.")
    filename = Path(upload.filename or "answer.webm").name
    suffix = Path(filename).suffix.lower()
    if suffix not in AUDIO_TYPES:
        raise ApiError(415, "unsupported_file", "Upload a WEBM, WAV, MP3, M4A, or OGG recording.")
    content = upload.stream.read(int(current_app.config["MAX_UPLOAD_BYTES"]) + 1)
    if not content:
        raise ApiError(400, "empty_file", "The recording is empty.")
    if len(content) > int(current_app.config["MAX_UPLOAD_BYTES"]):
        raise ApiError(413, "file_too_large", "Recordings must be 5 MB or smaller.")
    if duration_seconds is None or duration_seconds <= 0 or duration_seconds > 600:
        raise ApiError(422, "validation_error", "The recording duration is missing.")
    transcript = transcribe(content, AUDIO_TYPES[suffix])
    if len(transcript.strip()) < 2:
        raise ApiError(422, "no_speech", "No speech was detected in that recording.")
    fillers = count_fillers(transcript)
    words = len(re.findall(r"[A-Za-z0-9']+", transcript))
    wpm = round(words / (duration_seconds / 60), 1)
    score = communication_score(wpm, fillers["count"], words)
    parsed, _provider, _model = complete_json(
        FEEDBACK_INSTRUCTIONS,
        {
            "transcript": transcript[:4000],
            "words_per_minute": wpm,
            "filler_words": fillers["words"],
        },
    )
    feedback = require_text(parsed, "clarity_feedback")
    upload_dir = Path(current_app.config["UPLOAD_DIR"]) / "audio"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored = upload_dir / f"{uuid.uuid4()}{suffix}"
    stored.write_bytes(content)
    row = CommunicationAnalysis(
        student_id=student.id,
        session_id=session_id,
        turn_id=turn_id,
        audio_path=str(stored),
        transcript=transcript,
        duration_seconds=Decimal(f"{duration_seconds:.2f}"),
        words_per_minute=Decimal(f"{wpm:.1f}"),
        filler_count=fillers["count"],
        filler_words=fillers["words"],
        pause_count=None,
        clarity_feedback=feedback,
        communication_score=Decimal(f"{score:.2f}"),
    )
    db.session.add(row)
    db.session.flush()
    scoring.record_score(
        student.id,
        "communication",
        score,
        "communication_analysis",
        row.id,
        [feedback],
        list(fillers["words"].keys())[:5],
    )
    db.session.commit()
    return row


def list_analyses(student: User) -> list[CommunicationAnalysis]:
    from sqlalchemy import select

    return list(
        db.session.scalars(
            select(CommunicationAnalysis)
            .where(CommunicationAnalysis.student_id == student.id)
            .order_by(CommunicationAnalysis.created_at.desc())
        )
    )


def public_analysis(row: CommunicationAnalysis) -> dict:
    return {
        "id": str(row.id),
        "session_id": str(row.session_id) if row.session_id else None,
        "turn_id": str(row.turn_id) if row.turn_id else None,
        "transcript": row.transcript,
        "duration_seconds": float(row.duration_seconds),
        "words_per_minute": float(row.words_per_minute),
        "filler_count": row.filler_count,
        "filler_words": row.filler_words,
        "pause_count": row.pause_count,
        "clarity_feedback": row.clarity_feedback,
        "communication_score": float(row.communication_score),
        "created_at": row.created_at,
    }


def transcribe(content: bytes, mime_type: str) -> str:
    override = current_app.extensions.get("transcriber")
    if override is not None:
        text = override(content, mime_type)
        if not isinstance(text, str):
            raise ApiError(502, "speech_response_invalid", "The transcript could not be read.")
        return text.strip()
    provider = current_app.config["LLM_PROVIDER"]
    if provider == "openai" and current_app.config["OPENAI_API_KEY"].strip():
        return _whisper(content, mime_type)
    if provider == "gemini" and current_app.config["GEMINI_API_KEY"].strip():
        return _gemini_audio(content, mime_type)
    raise ApiError(
        503,
        "speech_not_configured",
        "Set the Gemini or OpenAI key before a recording can be transcribed.",
    )


def count_fillers(transcript: str) -> dict:
    lowered = transcript.lower()
    counts: dict[str, int] = {}
    for phrase in FILLER_PHRASES:
        found = len(re.findall(rf"\b{re.escape(phrase)}\b", lowered))
        if found:
            counts[phrase] = found
            lowered = re.sub(rf"\b{re.escape(phrase)}\b", " ", lowered)
    for word in FILLER_WORDS:
        found = len(re.findall(rf"\b{word}\b", lowered))
        if found:
            counts[word] = found
    return {"count": sum(counts.values()), "words": counts}


def communication_score(words_per_minute: float, filler_count: int, word_count: int) -> float:
    """Score measured pace and filler rate. This is not a voice-emotion score.

    A pace of 120 to 160 words per minute adds 15 points to a base of 70.
    Nearby paces add 5. Each filler per 100 words removes 8 points, up to 30.
    """
    score = 70.0
    if 120 <= words_per_minute <= 160:
        score += 15
    elif 90 <= words_per_minute < 120 or 160 < words_per_minute <= 190:
        score += 5
    else:
        score -= 10
    if word_count:
        score -= min(30, 8 * (filler_count / word_count) * 100)
    return float(max(0, min(100, round(score, 2))))


def _whisper(content: bytes, mime_type: str) -> str:
    try:
        response = httpx.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {current_app.config['OPENAI_API_KEY'].strip()}"},
            data={"model": "whisper-1"},
            files={"file": ("speech" + _suffix(mime_type), content, mime_type)},
            timeout=httpx.Timeout(60.0),
        )
    except httpx.HTTPError as exc:
        raise ApiError(502, "speech_provider_error", "Transcription failed. Try again.") from exc
    if response.status_code >= 400:
        raise ApiError(502, "speech_provider_error", "Transcription failed. Try again.")
    text = response.json().get("text")
    if not isinstance(text, str):
        raise ApiError(502, "speech_response_invalid", "The transcript could not be read.")
    return text.strip()


def _gemini_audio(content: bytes, mime_type: str) -> str:
    model = current_app.config["GEMINI_MODEL"].strip()
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "Transcribe the speech exactly. Return JSON with one key, transcript."},
                    {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(content).decode()}},
                ],
            }
        ],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    try:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": current_app.config["GEMINI_API_KEY"].strip()},
            json=body,
            timeout=httpx.Timeout(60.0),
        )
    except httpx.HTTPError as exc:
        raise ApiError(502, "speech_provider_error", "Transcription failed. Try again.") from exc
    if response.status_code >= 400:
        raise ApiError(502, "speech_provider_error", "Transcription failed. Try again.")
    try:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("The transcript could not be read.") from exc
    parsed = parse_json_object(text)
    return require_text(parsed, "transcript", max_length=8000)


def _suffix(mime_type: str) -> str:
    return next((suffix for suffix, mime in AUDIO_TYPES.items() if mime == mime_type), ".webm")

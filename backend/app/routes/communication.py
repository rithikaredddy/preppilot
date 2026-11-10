import uuid

from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.errors import ApiError
from app.schemas.catalog import CommunicationAnalysisSchema, CommunicationListSchema
from app.services import communication_service
from app.services.access import require_student

blp = Blueprint(
    "communication", __name__, url_prefix="/api/v1", description="Communication analysis"
)


@blp.route("/communication/analyses")
class CommunicationAnalyses(MethodView):
    @jwt_required()
    @blp.response(200, CommunicationListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List the signed-in student's communication analyses."""
        student = require_student()
        return {
            "items": [
                communication_service.public_analysis(row)
                for row in communication_service.list_analyses(student)
            ]
        }

    @jwt_required()
    @blp.response(201, CommunicationAnalysisSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self):
        """Transcribe a recording and store pace, filler, and clarity feedback."""
        student = require_student()
        upload = request.files.get("audio")
        if upload is None:
            raise ApiError(400, "file_required", "Record or upload an audio file.")
        analysis = communication_service.analyze(
            student,
            upload,
            _duration(request.form.get("duration_seconds", "")),
            _optional_uuid(request.form.get("session_id", ""), "session_id"),
            _optional_uuid(request.form.get("turn_id", ""), "turn_id"),
        )
        return communication_service.public_analysis(analysis)


def _duration(raw: str) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError(422, "validation_error", "The recording duration is missing.") from exc


def _optional_uuid(raw: str, name: str):
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return uuid.UUID(text)
    except ValueError as exc:
        raise ApiError(422, "validation_error", f"{name} is not a valid id.") from exc

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.practice import (
    AnswerSchema,
    InterviewListSchema,
    InterviewSchema,
    PageQuerySchema,
    StartInterviewSchema,
)
from app.services import interview_service
from app.services.access import require_student

blp = Blueprint("interviews", __name__, url_prefix="/api/v1", description="Mock interviews")


@blp.route("/interviews")
class Interviews(MethodView):
    @jwt_required()
    @blp.arguments(PageQuerySchema, location="query")
    @blp.response(200, InterviewListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, query):
        """List the signed-in student's interview sessions."""
        student = require_student()
        return interview_service.list_sessions(student, query["page"], query["page_size"])

    @jwt_required()
    @blp.arguments(StartInterviewSchema)
    @blp.response(201, InterviewSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data):
        """Start an HR or technical interview and store the first question."""
        student = require_student()
        session = interview_service.start_session(student, data)
        return interview_service.public_session(session, include_turns=True)


@blp.route("/interviews/<uuid:session_id>")
class InterviewDetail(MethodView):
    @jwt_required()
    @blp.response(200, InterviewSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, session_id):
        """Return one interview, including questions, answers, and evaluations."""
        student = require_student()
        session = interview_service.get_session(student, session_id)
        return interview_service.public_session(session, include_turns=True)


@blp.route("/interviews/<uuid:session_id>/answers")
class InterviewAnswer(MethodView):
    @jwt_required()
    @blp.arguments(AnswerSchema)
    @blp.response(200, InterviewSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data, session_id):
        """Store an answer, its evaluation, and any follow-up question."""
        student = require_student()
        session = interview_service.get_session(student, session_id)
        updated = interview_service.submit_answer(student, session, data["answer"])
        return interview_service.public_session(updated, include_turns=True)


@blp.route("/interviews/<uuid:session_id>/complete")
class InterviewComplete(MethodView):
    @jwt_required()
    @blp.response(200, InterviewSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, session_id):
        """Finish an interview and store scores computed from the turn evaluations."""
        student = require_student()
        session = interview_service.get_session(student, session_id)
        updated = interview_service.complete_session(student, session)
        return interview_service.public_session(updated, include_turns=True)

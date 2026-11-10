from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.catalog import (
    CodingProblemListSchema,
    CodingProblemSchema,
    CodingSubmissionListSchema,
    CodingSubmissionSchema,
    RunResultSchema,
    SubmitCodeSchema,
)
from app.schemas.practice import PageQuerySchema
from app.services import coding_service
from app.services.access import require_student

blp = Blueprint("coding", __name__, url_prefix="/api/v1", description="Coding assessment")


@blp.route("/coding/problems")
class CodingProblems(MethodView):
    @jwt_required()
    @blp.response(200, CodingProblemListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List curated coding problems. Hidden tests are not included."""
        require_student()
        return {"items": coding_service.list_problems()}


@blp.route("/coding/problems/<uuid:problem_id>")
class CodingProblemDetail(MethodView):
    @jwt_required()
    @blp.response(200, CodingProblemSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, problem_id):
        """Return one problem with public tests only."""
        require_student()
        return coding_service.public_problem(coding_service.get_problem(problem_id))


@blp.route("/coding/problems/<uuid:problem_id>/run")
class CodingRun(MethodView):
    @jwt_required()
    @blp.arguments(SubmitCodeSchema)
    @blp.response(200, RunResultSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data, problem_id):
        """Run public tests without saving a submission."""
        require_student()
        problem = coding_service.get_problem(problem_id)
        return coding_service.run_public(problem, data["language"], data["source_code"])


@blp.route("/coding/problems/<uuid:problem_id>/submit")
class CodingSubmit(MethodView):
    @jwt_required()
    @blp.arguments(SubmitCodeSchema)
    @blp.response(201, CodingSubmissionSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data, problem_id):
        """Run the program in the external sandbox and store the result."""
        student = require_student()
        problem = coding_service.get_problem(problem_id)
        submission = coding_service.submit(student, problem, data["language"], data["source_code"])
        return coding_service.public_submission(submission, include_results=True)


@blp.route("/coding/submissions")
class CodingSubmissions(MethodView):
    @jwt_required()
    @blp.arguments(PageQuerySchema, location="query")
    @blp.response(200, CodingSubmissionListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, query):
        """List the signed-in student's coding submissions."""
        student = require_student()
        return coding_service.list_submissions(student, query["page"], query["page_size"])


@blp.route("/coding/submissions/<uuid:submission_id>")
class CodingSubmissionDetail(MethodView):
    @jwt_required()
    @blp.response(200, CodingSubmissionSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, submission_id):
        """Return one submission, including public-test output."""
        student = require_student()
        submission = coding_service.get_submission(student, submission_id)
        return coding_service.public_submission(submission, include_results=True)

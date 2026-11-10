from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.catalog import (
    CompanyListSchema,
    CompanyQuestionListSchema,
    CompanyQuestionQuerySchema,
    GenerateQuestionsSchema,
)
from app.services import company_service
from app.services.access import require_student

blp = Blueprint("companies", __name__, url_prefix="/api/v1", description="Company preparation")


@blp.route("/companies")
class Companies(MethodView):
    @jwt_required()
    @blp.response(200, CompanyListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List companies with curated preparation material."""
        require_student()
        return {"items": company_service.list_companies()}


@blp.route("/companies/<string:slug>/questions")
class CompanyQuestions(MethodView):
    @jwt_required()
    @blp.arguments(CompanyQuestionQuerySchema, location="query")
    @blp.response(200, CompanyQuestionListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, query, slug):
        """List questions for one company. Each item is labeled curated or AI-generated."""
        require_student()
        return company_service.questions_for(
            slug, query["category"], query["difficulty"], query["source"]
        )


@blp.route("/companies/<string:slug>/practice-questions")
class CompanyPracticeQuestions(MethodView):
    @jwt_required()
    @blp.arguments(GenerateQuestionsSchema)
    @blp.response(201, CompanyQuestionListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data, slug):
        """Generate practice questions and store them as AI-generated."""
        require_student()
        return company_service.generate_questions(
            slug, data["category"], data["difficulty"], data["count"]
        )

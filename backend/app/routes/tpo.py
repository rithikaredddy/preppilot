from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.errors import ApiError
from app.schemas.auth import StudentListQuerySchema, StudentListSchema
from app.schemas.insights import InsightsSchema, StudentDetailSchema
from app.services import analytics, auth_service

blp = Blueprint("tpo", __name__, url_prefix="/api/v1/tpo", description="TPO oversight")


@blp.route("/students")
class Students(MethodView):
    @jwt_required()
    @blp.arguments(StudentListQuerySchema, location="query")
    @blp.response(200, StudentListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, query_args):
        """List students with a live readiness percentage. Transcripts are not included."""
        user = auth_service.load_user(get_jwt_identity())
        if user.role != "tpo":
            raise ApiError(403, "forbidden", "Only a TPO account can view the student list.")
        return analytics.list_for_tpo(
            page=query_args["page"],
            page_size=query_args["page_size"],
            branch=query_args["branch"],
            sort=query_args["sort"],
            readiness_below=query_args["readiness_below"],
        )


@blp.route("/insights")
class Insights(MethodView):
    @jwt_required()
    @blp.arguments(StudentListQuerySchema, location="query")
    @blp.response(200, InsightsSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, query_args):
        """Batch averages and the weak areas that show up most often."""
        user = auth_service.load_user(get_jwt_identity())
        if user.role != "tpo":
            raise ApiError(403, "forbidden", "Only a TPO account can view batch insights.")
        return analytics.batch_insights(query_args["branch"])


@blp.route("/students/<uuid:student_id>")
class StudentDetail(MethodView):
    @jwt_required()
    @blp.response(200, StudentDetailSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self, student_id):
        """Score breakdown for one student. Interview transcripts are not returned."""
        user = auth_service.load_user(get_jwt_identity())
        if user.role != "tpo":
            raise ApiError(403, "forbidden", "Only a TPO account can open a student breakdown.")
        return analytics.student_detail(student_id)

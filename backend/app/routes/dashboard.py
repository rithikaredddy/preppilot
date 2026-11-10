from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.errors import ApiError
from app.schemas.auth import DashboardSchema
from app.schemas.insights import AnalyticsSchema
from app.services import analytics, auth_service, scoring

blp = Blueprint(
    "dashboard", __name__, url_prefix="/api/v1/dashboard", description="Student dashboard"
)


@blp.route("/summary")
class Summary(MethodView):
    @jwt_required()
    @blp.response(200, DashboardSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Return the signed-in student's stored scores."""
        user = auth_service.load_user(get_jwt_identity())
        if user.role != "student":
            raise ApiError(403, "forbidden", "Only students can view this dashboard.")
        return scoring.dashboard_summary(user.id)


@blp.route("/analytics")
class Analytics(MethodView):
    @jwt_required()
    @blp.response(200, AnalyticsSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Return charts, weak areas, and the preparation gap."""
        user = auth_service.load_user(get_jwt_identity())
        if user.role != "student":
            raise ApiError(403, "forbidden", "Only students can view this dashboard.")
        return analytics.analytics(user.id)

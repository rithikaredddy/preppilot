from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.insights import RoadmapItemSchema, RoadmapListSchema, RoadmapUpdateSchema
from app.services import roadmap_service
from app.services.access import require_student

blp = Blueprint("roadmap", __name__, url_prefix="/api/v1", description="Learning roadmap")


@blp.route("/roadmap")
class Roadmap(MethodView):
    @jwt_required()
    @blp.response(200, RoadmapListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """List the student's roadmap items."""
        student = require_student()
        return roadmap_service.list_items(student)

    @jwt_required()
    @blp.response(201, RoadmapListSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self):
        """Build a study plan from weak areas and the readiness factors."""
        student = require_student()
        return roadmap_service.generate(student)


@blp.route("/roadmap/<uuid:item_id>")
class RoadmapItem(MethodView):
    @jwt_required()
    @blp.arguments(RoadmapUpdateSchema)
    @blp.response(200, RoadmapItemSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def patch(self, data, item_id):
        """Mark one roadmap item complete or incomplete."""
        student = require_student()
        return roadmap_service.set_complete(student, item_id, data["is_complete"])

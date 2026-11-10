from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.schemas.insights import ReadinessSchema, ReadinessViewSchema, WhatIfSchema
from app.services import readiness
from app.services.access import require_student

blp = Blueprint("readiness", __name__, url_prefix="/api/v1", description="Placement readiness")


@blp.route("/readiness")
class Readiness(MethodView):
    @jwt_required()
    @blp.response(200, ReadinessViewSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Return the current readiness estimate and the stored trend."""
        student = require_student()
        return readiness.predict_and_store(student.id)


@blp.route("/readiness/what-if")
class WhatIf(MethodView):
    @jwt_required()
    @blp.arguments(WhatIfSchema)
    @blp.response(200, ReadinessSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def post(self, data):
        """Score a hypothetical set of inputs without saving them."""
        require_student()
        return readiness.what_if(data)

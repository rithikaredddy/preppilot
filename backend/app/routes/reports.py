from flask import send_file
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.services import report_service
from app.services.access import require_student

blp = Blueprint("reports", __name__, url_prefix="/api/v1", description="Performance reports")


@blp.route("/reports/performance")
class PerformanceReport(MethodView):
    @jwt_required()
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Download a PDF of the student's scores, readiness, and suggestions."""
        student = require_student()
        return send_file(
            report_service.build_for(student),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="placement-report.pdf",
        )

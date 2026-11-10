from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import text

from app.extensions import db

blp = Blueprint("health", __name__, url_prefix="/api/v1", description="Service health")


@blp.route("/health")
class Health(MethodView):
    def get(self):
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            return jsonify(status="degraded", database="unavailable"), 503
        return jsonify(status="ok", database="ok")

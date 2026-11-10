import logging

from flask import Flask, jsonify
from flask_smorest import Api
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import load_settings
from app.errors import ApiError, error_body
from app.extensions import cors, db, jwt, migrate


def create_app(config_name: str = "development") -> Flask:
    testing = config_name == "testing"
    app = Flask(__name__)
    app.config.update(load_settings(testing=testing))

    if not testing:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )

    if app.config["ENV_NAME"] == "production":
        # Render, Railway and Fly sit behind one proxy; trust its client IP and scheme
        # so login throttling counts real addresses.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    if not testing:
        migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from app import models  # noqa: F401

    api = Api(app)
    from app.routes.auth import blp as auth_blp
    from app.routes.coding import blp as coding_blp
    from app.routes.communication import blp as communication_blp
    from app.routes.companies import blp as companies_blp
    from app.routes.dashboard import blp as dashboard_blp
    from app.routes.health import blp as health_blp
    from app.routes.interviews import blp as interviews_blp
    from app.routes.profile import blp as profile_blp
    from app.routes.readiness import blp as readiness_blp
    from app.routes.reports import blp as reports_blp
    from app.routes.resumes import blp as resumes_blp
    from app.routes.roadmap import blp as roadmap_blp
    from app.routes.tpo import blp as tpo_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(profile_blp)
    api.register_blueprint(dashboard_blp)
    api.register_blueprint(tpo_blp)
    api.register_blueprint(resumes_blp)
    api.register_blueprint(interviews_blp)
    api.register_blueprint(coding_blp)
    api.register_blueprint(companies_blp)
    api.register_blueprint(communication_blp)
    api.register_blueprint(readiness_blp)
    api.register_blueprint(roadmap_blp)
    api.register_blueprint(reports_blp)

    register_jwt_handlers()
    register_error_handlers(app)
    return app


def register_jwt_handlers() -> None:
    @jwt.unauthorized_loader
    def unauthorized(_reason: str):
        return jsonify(error_body("unauthorized", "Authentication is required.")), 401

    @jwt.invalid_token_loader
    def invalid(_reason: str):
        return jsonify(error_body("invalid_token", "The access token is not valid.")), 401

    @jwt.expired_token_loader
    def expired(_header, _payload):
        return jsonify(error_body("token_expired", "The access token has expired.")), 401


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api(error: ApiError):
        return jsonify(error_body(error.error_code, error.description, error.details)), error.code

    @app.errorhandler(HTTPException)
    def handle_http(error: HTTPException):
        data = getattr(error, "data", None)
        if error.code == 422 and isinstance(data, dict):
            messages = data.get("messages", {})
            raw = messages.get("json") or messages.get("query") or messages.get("form") or {}
            details = _flatten_errors(raw)
            detail_text = "; ".join(
                f"{name}: {', '.join(messages)}" for name, messages in details.items() if messages
            )
            return jsonify(
                error_body(
                    "validation_error",
                    detail_text or "Check the highlighted fields.",
                    details,
                )
            ), 422
        if error.response is not None:
            return error.response
        return jsonify(
            error_body("http_error", error.description or "Request failed.")
        ), error.code or 500


def _flatten_errors(raw: dict) -> dict[str, list[str]]:
    details: dict[str, list[str]] = {}
    if not isinstance(raw, dict):
        return {"_schema": [str(raw)]}
    for key, value in raw.items():
        if isinstance(value, list):
            details[str(key)] = [str(item) for item in value]
        elif isinstance(value, dict):
            nested = _flatten_errors(value)
            details[str(key)] = [item for messages in nested.values() for item in messages] or [
                str(value)
            ]
        else:
            details[str(key)] = [str(value)]
    return details

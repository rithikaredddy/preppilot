from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.schemas.auth import ProfileUpdateSchema, UserSchema
from app.services import auth_service

blp = Blueprint("profile", __name__, url_prefix="/api/v1", description="Profile")


@blp.route("/profile")
class Profile(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Return the signed-in profile."""
        user = auth_service.load_user(get_jwt_identity())
        return auth_service.public_user(user)

    @jwt_required()
    @blp.arguments(ProfileUpdateSchema)
    @blp.response(200, UserSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def patch(self, data):
        """Update the signed-in profile."""
        user = auth_service.load_user(get_jwt_identity())
        return auth_service.update_profile(user, data)

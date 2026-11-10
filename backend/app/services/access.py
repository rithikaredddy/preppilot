from flask_jwt_extended import get_jwt_identity

from app.errors import ApiError
from app.services import auth_service


def require_student():
    user = auth_service.load_user(get_jwt_identity())
    if user.role != "student":
        raise ApiError(403, "forbidden", "Only students can use this.")
    return user

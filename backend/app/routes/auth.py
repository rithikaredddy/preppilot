from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.schemas.auth import (
    AuthResponseSchema,
    ForgotPasswordSchema,
    LoginSchema,
    LogoutSchema,
    MessageSchema,
    RegisterSchema,
    ResetPasswordSchema,
    TokenPairSchema,
    UserSchema,
)
from app.services import auth_service

blp = Blueprint("auth", __name__, url_prefix="/api/v1/auth", description="Authentication")


@blp.route("/register")
class Register(MethodView):
    @blp.arguments(RegisterSchema)
    @blp.response(201, AuthResponseSchema)
    def post(self, data):
        """Create a student account, or a TPO account after the email code is verified."""
        return auth_service.register_user(data)


@blp.route("/tpo-otp")
class TpoOtp(MethodView):
    @blp.arguments(ForgotPasswordSchema)
    @blp.response(200, MessageSchema)
    def post(self, data):
        """Email a 6-digit code for TPO registration."""
        return auth_service.request_tpo_otp(data["email"])


@blp.route("/login")
class Login(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, AuthResponseSchema)
    def post(self, data):
        """Sign in with email and password."""
        return auth_service.authenticate(data["email"], data["password"])


@blp.route("/refresh")
class Refresh(MethodView):
    @jwt_required(refresh=True)
    @blp.response(200, TokenPairSchema)
    def post(self):
        """Exchange a refresh token for a new access token and refresh token."""
        from flask import request

        header = request.headers.get("Authorization", "")
        raw = header.split(" ", 1)[1].strip() if " " in header else ""
        user = auth_service.load_user(get_jwt_identity())
        return auth_service.rotate_refresh_token(raw, user)


@blp.route("/logout")
class Logout(MethodView):
    @blp.arguments(LogoutSchema)
    @blp.response(200, MessageSchema)
    def post(self, data):
        """Revoke a refresh token."""
        auth_service.revoke_refresh_token(data["refresh_token"])
        return {"message": "Signed out."}


@blp.route("/forgot-password")
class ForgotPassword(MethodView):
    @blp.arguments(ForgotPasswordSchema)
    @blp.response(200, MessageSchema)
    def post(self, data):
        """Request a password reset link."""
        return auth_service.request_password_reset(data["email"])


@blp.route("/reset-password")
class ResetPassword(MethodView):
    @blp.arguments(ResetPasswordSchema)
    @blp.response(200, MessageSchema)
    def post(self, data):
        """Set a new password using a reset token."""
        auth_service.reset_password(data["token"], data["password"])
        return {"message": "Your password has been updated."}


@blp.route("/me")
class Me(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    @blp.doc(security=[{"bearerAuth": []}])
    def get(self):
        """Return the signed-in account."""
        user = auth_service.load_user(get_jwt_identity())
        return auth_service.public_user(user)

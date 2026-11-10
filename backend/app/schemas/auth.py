from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)


def _password_rules(value: str) -> None:
    if len(value.encode("utf-8")) > 72:
        raise ValidationError("Password must be at most 72 bytes.")
    if not any(character.isalpha() for character in value) or not any(
        character.isdigit() for character in value
    ):
        raise ValidationError("Use at least one letter and one number.")


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))
    role = fields.String(required=True, validate=validate.OneOf(["student", "tpo"]))
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    roll_number = fields.String(
        required=False, allow_none=True, validate=validate.Length(min=2, max=32)
    )
    branch = fields.String(required=False, allow_none=True, validate=validate.Length(min=2, max=80))
    graduation_year = fields.Integer(
        required=False, allow_none=True, validate=validate.Range(min=2000, max=2040)
    )
    department = fields.String(
        required=False, allow_none=True, validate=validate.Length(min=2, max=120)
    )
    designation = fields.String(
        required=False, allow_none=True, validate=validate.Length(min=2, max=120)
    )
    otp = fields.String(required=False, allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @validates("password")
    def check_password(self, value: str, **_kwargs) -> None:
        _password_rules(value)

    @validates_schema
    def check_role_fields(self, data: dict, **_kwargs) -> None:
        errors: dict[str, list[str]] = {}
        if data.get("role") == "student":
            for field_name in ("roll_number", "branch", "graduation_year"):
                if data.get(field_name) in (None, ""):
                    errors[field_name] = ["This field is required for students."]
        if data.get("role") == "tpo":
            for field_name in ("department", "designation"):
                if not (data.get(field_name) or "").strip():
                    errors[field_name] = ["This field is required for TPO accounts."]
            otp = (data.get("otp") or "").strip()
            if not otp.isdigit() or len(otp) != 6:
                errors["otp"] = ["Enter the 6-digit code sent to this email."]
        if errors:
            raise ValidationError(errors)


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1, max=128))

    class Meta:
        unknown = EXCLUDE


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)

    class Meta:
        unknown = EXCLUDE


class ResetPasswordSchema(Schema):
    token = fields.String(required=True, validate=validate.Length(min=10, max=256))
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))

    class Meta:
        unknown = EXCLUDE

    @validates("password")
    def check_password(self, value: str, **_kwargs) -> None:
        _password_rules(value)


class LogoutSchema(Schema):
    refresh_token = fields.String(required=True)

    class Meta:
        unknown = EXCLUDE


class ProfileUpdateSchema(Schema):
    full_name = fields.String(required=False, validate=validate.Length(min=2, max=120))
    roll_number = fields.String(required=False, validate=validate.Length(min=2, max=32))
    branch = fields.String(required=False, validate=validate.Length(min=2, max=80))
    graduation_year = fields.Integer(required=False, validate=validate.Range(min=2000, max=2040))
    cgpa = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0, max=10))
    backlogs = fields.Integer(
        required=False, allow_none=True, validate=validate.Range(min=0, max=40)
    )
    internship_count = fields.Integer(
        required=False, allow_none=True, validate=validate.Range(min=0, max=20)
    )
    certification_count = fields.Integer(
        required=False, allow_none=True, validate=validate.Range(min=0, max=40)
    )
    project_count = fields.Integer(
        required=False, allow_none=True, validate=validate.Range(min=0, max=40)
    )
    phone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    target_companies = fields.String(
        required=False, allow_none=True, validate=validate.Length(max=240)
    )
    department = fields.String(required=False, validate=validate.Length(min=2, max=120))
    designation = fields.String(required=False, validate=validate.Length(min=2, max=120))

    class Meta:
        unknown = EXCLUDE


class UserSchema(Schema):
    id = fields.String(required=True)
    email = fields.Email(required=True)
    role = fields.String(required=True)
    full_name = fields.String(required=True)
    roll_number = fields.String(allow_none=True)
    branch = fields.String(allow_none=True)
    graduation_year = fields.Integer(allow_none=True)
    cgpa = fields.Float(allow_none=True)
    backlogs = fields.Integer(allow_none=True)
    internship_count = fields.Integer(allow_none=True)
    certification_count = fields.Integer(allow_none=True)
    project_count = fields.Integer(allow_none=True)
    phone = fields.String(allow_none=True)
    target_companies = fields.String(allow_none=True)
    department = fields.String(allow_none=True)
    designation = fields.String(allow_none=True)


class AuthResponseSchema(Schema):
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    user = fields.Nested(UserSchema, required=True)


class TokenPairSchema(Schema):
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)


class MessageSchema(Schema):
    message = fields.String(required=True)
    reset_token = fields.String(required=False)
    otp = fields.String(required=False)


class DashboardSchema(Schema):
    resume_score = fields.Float(allow_none=True)
    hr_score = fields.Float(allow_none=True)
    technical_score = fields.Float(allow_none=True)
    coding_score = fields.Float(allow_none=True)
    communication_score = fields.Float(allow_none=True)
    completed_sessions = fields.Integer(required=True)


class StudentListQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=50))
    branch = fields.String(load_default="")
    sort = fields.String(
        load_default="name",
        validate=validate.OneOf(["name", "branch", "roll_number", "readiness"]),
    )
    readiness_below = fields.Integer(
        load_default=None, allow_none=True, validate=validate.Range(min=0, max=100)
    )

    class Meta:
        unknown = EXCLUDE


class StudentListItemSchema(Schema):
    id = fields.String(required=True)
    full_name = fields.String(required=True)
    email = fields.Email(required=True)
    roll_number = fields.String(required=True)
    branch = fields.String(required=True)
    graduation_year = fields.Integer(required=True)
    readiness_percentage = fields.Float(allow_none=True)
    top_factor = fields.String(allow_none=True)


class StudentListSchema(Schema):
    items = fields.List(fields.Nested(StudentListItemSchema), required=True)
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    total = fields.Integer(required=True)

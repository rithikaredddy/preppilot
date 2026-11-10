import hashlib
import hmac
import logging
import secrets
import smtplib
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.message import EmailMessage

from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.errors import ApiError
from app.extensions import db
from app.models import EmailOtp, PasswordResetToken, RefreshToken, StudentProfile, TpoProfile, User

logger = logging.getLogger(__name__)

STUDENT_FIELDS = {
    "full_name",
    "roll_number",
    "branch",
    "graduation_year",
    "cgpa",
    "backlogs",
    "internship_count",
    "certification_count",
    "project_count",
    "phone",
    "target_companies",
}
TPO_FIELDS = {"full_name", "department", "designation"}


def hash_password(password: str) -> str:
    return bcrypt_hash(password)


def bcrypt_hash(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def public_user(user: User) -> dict:
    payload = {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "full_name": None,
        "roll_number": None,
        "branch": None,
        "graduation_year": None,
        "cgpa": None,
        "backlogs": None,
        "internship_count": None,
        "certification_count": None,
        "project_count": None,
        "phone": None,
        "target_companies": None,
        "department": None,
        "designation": None,
    }
    if user.role == "student" and user.student_profile is not None:
        profile = user.student_profile
        payload.update(
            {
                "full_name": profile.full_name,
                "roll_number": profile.roll_number,
                "branch": profile.branch,
                "graduation_year": profile.graduation_year,
                "cgpa": float(profile.cgpa) if profile.cgpa is not None else None,
                "backlogs": profile.backlogs,
                "internship_count": profile.internship_count,
                "certification_count": profile.certification_count,
                "project_count": profile.project_count,
                "phone": profile.phone,
                "target_companies": profile.target_companies,
            }
        )
    if user.role == "tpo" and user.tpo_profile is not None:
        profile = user.tpo_profile
        payload.update(
            {
                "full_name": profile.full_name,
                "department": profile.department,
                "designation": profile.designation,
            }
        )
    return payload


def load_user(user_id: str) -> User:
    try:
        parsed = uuid_or_none(user_id)
    except ValueError as exc:
        raise ApiError(401, "unauthorized", "Authentication is required.") from exc
    user = db.session.get(User, parsed)
    if user is None or not user.is_active:
        raise ApiError(401, "unauthorized", "Authentication is required.")
    return user


def uuid_or_none(value: str):
    import uuid

    return uuid.UUID(value)


def register_user(data: dict) -> dict:
    email = data["email"].strip().lower()
    role = data["role"]
    otp_row = None
    if role == "tpo":
        otp_row = _match_tpo_otp(email, (data.get("otp") or "").strip())

    existing = db.session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(409, "email_taken", "An account with this email already exists.")

    user = User(email=email, password_hash=bcrypt_hash(data["password"]), role=role)
    if role == "student":
        roll_number = data["roll_number"].strip().upper()
        taken = db.session.scalar(
            select(StudentProfile).where(
                func.lower(StudentProfile.roll_number) == roll_number.lower()
            )
        )
        if taken is not None:
            raise ApiError(409, "roll_taken", "A student with this roll number already exists.")
        user.student_profile = StudentProfile(
            full_name=data["full_name"].strip(),
            roll_number=roll_number,
            branch=data["branch"].strip(),
            graduation_year=data["graduation_year"],
        )
    else:
        user.tpo_profile = TpoProfile(
            full_name=data["full_name"].strip(),
            department=data["department"].strip(),
            designation=data["designation"].strip(),
        )

    if otp_row is not None:
        otp_row.used_at = datetime.now(timezone.utc)
    db.session.add(user)
    try:
        db.session.flush()
        access_token, refresh_token = issue_tokens(user)
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError(409, "conflict", "An account with these details already exists.") from exc
    return {"access_token": access_token, "refresh_token": refresh_token, "user": public_user(user)}


_failed_logins: dict[str, deque] = defaultdict(deque)
_failed_lock = threading.Lock()


def _login_key(email: str) -> str:
    return f"{request.remote_addr or 'unknown'}|{email}"


def _recent_failures(key: str, now: float) -> deque:
    window = current_app.config["LOGIN_LOCKOUT_MINUTES"] * 60
    attempts = _failed_logins[key]
    while attempts and now - attempts[0] > window:
        attempts.popleft()
    return attempts


def authenticate(email: str, password: str) -> dict:
    """Sign in, refusing further attempts after repeated failures from one address.

    The counter lives in process memory, which suits a single server. A
    multi-instance deployment would move it to Redis or the database.
    """
    normalized = email.strip().lower()
    key = _login_key(normalized)
    now = datetime.now(timezone.utc).timestamp()
    limit = current_app.config["LOGIN_MAX_FAILURES"]
    with _failed_lock:
        attempts = _recent_failures(key, now)
        if len(attempts) >= limit:
            window = current_app.config["LOGIN_LOCKOUT_MINUTES"] * 60
            minutes = max(1, int((window - (now - attempts[0])) // 60) + 1)
            raise ApiError(
                429,
                "too_many_attempts",
                f"Too many failed sign-ins. Try again in {minutes} minute"
                f"{'' if minutes == 1 else 's'}, or reset your password.",
            )
    user = db.session.scalar(select(User).where(User.email == normalized))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        with _failed_lock:
            _failed_logins[key].append(now)
        raise ApiError(401, "invalid_credentials", "The email or password is incorrect.")
    with _failed_lock:
        _failed_logins.pop(key, None)
    access_token, refresh_token = issue_tokens(user)
    return {"access_token": access_token, "refresh_token": refresh_token, "user": public_user(user)}


def issue_tokens(user: User) -> tuple[str, str]:
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=str(user.id))
    payload = decode_token(refresh_token)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.session.add(
        RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires_at)
    )
    db.session.commit()
    return access_token, refresh_token


def rotate_refresh_token(raw_token: str, user: User) -> dict:
    row = db.session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    if row is None or row.user_id != user.id or row.revoked_at is not None:
        raise ApiError(401, "invalid_refresh", "The refresh token is not valid.")
    if as_utc(row.expires_at) <= datetime.now(timezone.utc):
        raise ApiError(401, "invalid_refresh", "The refresh token is not valid.")
    row.revoked_at = datetime.now(timezone.utc)
    access_token, refresh_token = issue_tokens(user)
    return {"access_token": access_token, "refresh_token": refresh_token}


def revoke_refresh_token(raw_token: str) -> None:
    row = db.session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.session.commit()


def request_password_reset(email: str) -> dict:
    message = "If an account exists for that email, a reset link has been sent."
    user = db.session.scalar(select(User).where(User.email == email.strip().lower()))
    response = {"message": message}
    if user is None or not user.is_active:
        return response

    db.session.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=datetime.now(timezone.utc))
    )
    raw_token = secrets.token_urlsafe(32)
    db.session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
    )
    db.session.commit()
    link = f"{current_app.config['FRONTEND_URL'].rstrip('/')}/reset-password?token={raw_token}"
    send_reset_email(user.email, link)
    if _expose_reset_token():
        response["reset_token"] = raw_token
    return response


def reset_password(raw_token: str, password: str) -> None:
    row = db.session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw_token))
    )
    now = datetime.now(timezone.utc)
    if row is None or row.used_at is not None or as_utc(row.expires_at) <= now:
        raise ApiError(400, "invalid_reset", "This reset link is invalid or has expired.")
    user = db.session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise ApiError(400, "invalid_reset", "This reset link is invalid or has expired.")
    user.password_hash = bcrypt_hash(password)
    user.updated_at = now
    row.used_at = now
    db.session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.session.commit()


def update_profile(user: User, data: dict) -> dict:
    if not data:
        raise ApiError(422, "validation_error", "Provide at least one profile field to update.")
    allowed = STUDENT_FIELDS if user.role == "student" else TPO_FIELDS
    rejected = sorted(set(data) - allowed)
    if rejected:
        raise ApiError(
            422,
            "validation_error",
            "Some fields do not apply to this account.",
            {field: ["This field cannot be changed for your role."] for field in rejected},
        )

    profile = user.student_profile if user.role == "student" else user.tpo_profile
    if profile is None:
        raise ApiError(404, "profile_missing", "This account has no profile.")

    if "roll_number" in data:
        roll_number = data["roll_number"].strip().upper()
        taken = db.session.scalar(
            select(StudentProfile).where(
                func.lower(StudentProfile.roll_number) == roll_number.lower(),
                StudentProfile.user_id != user.id,
            )
        )
        if taken is not None:
            raise ApiError(409, "roll_taken", "A student with this roll number already exists.")
        data["roll_number"] = roll_number

    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        if key == "cgpa" and value is not None:
            value = Decimal(str(round(value, 2)))
        if key in {"full_name", "branch", "department", "designation"} and value == "":
            raise ApiError(
                422,
                "validation_error",
                "Check the highlighted fields.",
                {key: ["This field cannot be empty."]},
            )
        setattr(profile, key, value)

    now = datetime.now(timezone.utc)
    profile.updated_at = now
    user.updated_at = now
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ApiError(409, "conflict", "Those profile details are already in use.") from exc
    db.session.refresh(user)
    return public_user(user)


def list_students(*, page: int, page_size: int, branch: str, sort: str) -> dict:
    filters = [User.role == "student", User.is_active.is_(True)]
    if branch.strip():
        filters.append(func.lower(StudentProfile.branch) == branch.strip().lower())

    total = db.session.scalar(
        select(func.count())
        .select_from(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .where(*filters)
    )
    sort_column = {
        "name": StudentProfile.full_name,
        "branch": StudentProfile.branch,
        "roll_number": StudentProfile.roll_number,
    }[sort]
    rows = db.session.execute(
        select(User, StudentProfile)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .where(*filters)
        .order_by(sort_column.asc(), StudentProfile.roll_number.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [
            {
                "id": str(user.id),
                "full_name": profile.full_name,
                "email": user.email,
                "roll_number": profile.roll_number,
                "branch": profile.branch,
                "graduation_year": profile.graduation_year,
            }
            for user, profile in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": int(total or 0),
    }


def request_tpo_otp(email: str) -> dict:
    normalized = email.strip().lower()
    allowed = current_app.config.get("TPO_ALLOWED_EMAILS") or []
    if allowed and normalized not in allowed:
        raise ApiError(
            403, "tpo_email_not_allowed", "This email is not allowed to register as a TPO."
        )
    existing = db.session.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        raise ApiError(409, "email_taken", "This email already has an account. Sign in instead.")
    mail_configured = bool(current_app.config.get("SMTP_HOST"))
    message = (
        "A 6-digit code was sent to that email."
        if mail_configured
        else "Email is not set up on this computer, so the code is shown on this page."
    )
    response = {"message": message}

    latest = db.session.scalar(
        select(EmailOtp)
        .where(EmailOtp.email == normalized, EmailOtp.purpose == "tpo_register")
        .order_by(EmailOtp.created_at.desc())
    )
    now = datetime.now(timezone.utc)
    if (
        latest is not None
        and latest.used_at is None
        and (now - as_utc(latest.created_at)).total_seconds() < 60
    ):
        raise ApiError(429, "otp_cooldown", "Wait a minute before requesting another code.")

    db.session.execute(
        update(EmailOtp)
        .where(
            EmailOtp.email == normalized,
            EmailOtp.purpose == "tpo_register",
            EmailOtp.used_at.is_(None),
        )
        .values(used_at=now)
    )
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.session.add(
        EmailOtp(
            email=normalized,
            purpose="tpo_register",
            code_hash=hash_token(code),
            expires_at=now + timedelta(minutes=10),
        )
    )
    db.session.commit()
    send_otp_email(normalized, code)
    if _expose_reset_token():
        response["otp"] = code
    return response


def _match_tpo_otp(email: str, code: str) -> EmailOtp:
    row = db.session.scalar(
        select(EmailOtp)
        .where(
            EmailOtp.email == email,
            EmailOtp.purpose == "tpo_register",
            EmailOtp.used_at.is_(None),
        )
        .order_by(EmailOtp.created_at.desc())
    )
    now = datetime.now(timezone.utc)
    invalid = ApiError(400, "invalid_otp", "The verification code is invalid or has expired.")
    if row is None or as_utc(row.expires_at) <= now or row.attempts >= 5:
        raise invalid
    if not hmac.compare_digest(hash_token(code), row.code_hash):
        row.attempts += 1
        db.session.commit()
        raise invalid
    return row


def send_otp_email(recipient: str, code: str) -> None:
    _send_email(
        recipient,
        "Your Interview Prep verification code",
        "Your TPO registration code is "
        f"{code}. It expires in 10 minutes.\n\n"
        "If you did not request this, you can ignore the email.",
        f"TPO verification code for {recipient}: {code}",
    )


def send_reset_email(recipient: str, link: str) -> None:
    _send_email(
        recipient,
        "Reset your Interview Prep password",
        "Use this link within 30 minutes to choose a new password:\n\n"
        f"{link}\n\n"
        "If you did not request this, you can ignore the email.",
        f"Password reset link for {recipient}: {link}",
    )


def _send_email(recipient: str, subject: str, body: str, dev_log: str) -> None:
    host = current_app.config.get("SMTP_HOST") or ""
    if not host:
        if current_app.config.get("ENV_NAME") != "production":
            logger.info(dev_log)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config.get("SMTP_FROM") or current_app.config.get("SMTP_USERNAME")
    message["To"] = recipient
    message.set_content(body)
    try:
        with smtplib.SMTP(host, current_app.config["SMTP_PORT"], timeout=10) as smtp:
            smtp.starttls()
            username = current_app.config.get("SMTP_USERNAME") or ""
            password = current_app.config.get("SMTP_PASSWORD") or ""
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    except Exception:
        logger.exception("Could not send email to %s", recipient)


def _expose_reset_token() -> bool:
    if current_app.config.get("ENV_NAME") == "production":
        return False
    return bool(current_app.config.get("PASSWORD_RESET_DEV_EXPOSE"))

from werkzeug.exceptions import HTTPException


class ApiError(HTTPException):
    def __init__(self, status: int, error_code: str, message: str, details: dict | None = None):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(description=message)
        self.code = status


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}

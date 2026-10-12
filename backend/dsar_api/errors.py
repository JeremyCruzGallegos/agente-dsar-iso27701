"""Errores de dominio y respuestas JSON uniformes."""
from __future__ import annotations

from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class ValidationError(ApiError):
    status_code = 422
    code = "validation_error"


class ConflictError(ApiError):
    status_code = 409
    code = "conflict"


class UnauthorizedError(ApiError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(ApiError):
    status_code = 403
    code = "forbidden"


def error_response(code: str, message: str, status_code: int):
    return jsonify({"status": "error", "error": {"code": code, "message": message}}), status_code


def ok(data=None, status_code: int = 200, **extra):
    body = {"status": "success", "data": data}
    body.update(extra)
    return jsonify(body), status_code


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def _api_error(err: ApiError):
        return error_response(err.code, err.message, err.status_code)

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        return error_response(err.name.lower().replace(" ", "_"), err.description or err.name, err.code or 500)

    @app.errorhandler(Exception)
    def _unexpected(err: Exception):
        app.logger.exception("Error no controlado")
        return error_response("internal_error", "Error interno del servidor.", 500)

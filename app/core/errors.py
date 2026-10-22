import re
from typing import Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[list[dict[str, Any]]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(message)


class BadRequest(AppError):
    def __init__(self, message: str = "Bad request", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(400, "bad_request", message, details)


class InvalidCursor(AppError):
    def __init__(self, message: str = "Invalid cursor", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(400, "invalid_cursor", message, details)


class Forbidden(AppError):
    def __init__(self, message: str = "Forbidden", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(403, "forbidden", message, details)


class NotFound(AppError):
    def __init__(self, message: str = "Not found", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(404, "not_found", message, details)


class WrongScreenType(AppError):
    def __init__(self, message: str = "Wrong screen type", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(404, "wrong_screen_type", message, details)


class SchemaStale(AppError):
    def __init__(self, message: str = "Schema is stale", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(409, "schema_stale", message, details)


class Conflict(AppError):
    def __init__(self, message: str = "Conflict error", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(409, "conflict", message, details)


class ValidationFailed(AppError):
    def __init__(self, message: str = "Validation failed", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(422, "validation_failed", message, details)


class InvalidSort(AppError):
    def __init__(self, message: str = "Invalid sort column", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(422, "invalid_sort", message, details)


class InvalidFilter(AppError):
    def __init__(self, message: str = "Invalid filter", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(422, "invalid_filter", message, details)


class ResultTooLarge(AppError):
    def __init__(self, message: str = "Result too large", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(422, "result_too_large", message, details)


class RuleViolation(AppError):
    def __init__(self, message: str = "Rule violation", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(422, "rule_violation", message, details)


class ConfigError(AppError):
    def __init__(self, message: str = "Configuration error", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(500, "config_error", message, details)


class InternalError(AppError):
    def __init__(self, message: str = "Internal server error", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(500, "internal_error", message, details)


class NotImplementedYet(AppError):
    def __init__(self, message: str = "Not implemented", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(501, "not_implemented", message, details)


class DbUnavailable(AppError):
    def __init__(self, message: str = "Database unavailable", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(503, "db_unavailable", message, details)


class QueryTimeout(AppError):
    def __init__(self, message: str = "Query timeout", details: Optional[list[dict[str, Any]]] = None):
        super().__init__(504, "query_timeout", message, details)


ERROR_RESPONSES = {
    400: {"description": "Bad Request / Invalid Cursor"},
    401: {"description": "Unauthorized"},
    403: {"description": "Forbidden"},
    404: {"description": "Not Found / Wrong Screen Type"},
    409: {"description": "Conflict / Schema Stale"},
    422: {"description": "Validation Failed / Rule Violation / Invalid Sort/Filter / Result Too Large"},
    500: {"description": "Config Error / Internal Error"},
    501: {"description": "Not Implemented"},
    503: {"description": "Database Unavailable"},
    504: {"description": "Query Timeout"},
}


def clean_raiserror_message(msg: str) -> str:
    cleaned = re.sub(r"\[Microsoft\]\[ODBC Driver[^\]]+\](?:\[SQL Server\])?", "", msg)
    cleaned = re.sub(r"\s*\(\d+\)\s*(?:\(SQLExecDirectW\))?", "", cleaned)
    cleaned = " ".join(cleaned.split()).strip()
    if len(cleaned) > 300:
        cleaned = cleaned[:300]
    return cleaned or "Rule violation"


def map_db_error(exc: Exception) -> AppError:
    err_str = str(exc)
    if hasattr(exc, "orig") and exc.orig:
        err_str = str(exc.orig)

    match_num = re.search(r"\[SQL Server\].*?\((\d+)\)", err_str)
    err_num = int(match_num.group(1)) if match_num else None

    sqlstate = ""
    if hasattr(exc, "orig") and exc.orig and hasattr(exc.orig, "args") and exc.orig.args:
        if isinstance(exc.orig.args[0], str):
            sqlstate = exc.orig.args[0]

    if err_num == 1205:
        return Conflict("Please try again")
    if err_num == 1222:
        return Conflict("The record is being edited by someone else")
    if err_num in (2627, 2601):
        return Conflict("Unique constraint violation")
    if err_num == 547:
        return Conflict("Foreign key or check constraint violation")
    if err_num == 515:
        col_match = re.search(r"column '([^']+)'", err_str)
        col = col_match.group(1) if col_match else None
        details = [{"field": col, "code": "required", "problem": "Field is required"}] if col else []
        return ValidationFailed("Required field missing", details)
    if err_num == 8152:
        return ValidationFailed("String or binary data would be truncated", [{"code": "too_long"}])
    if err_num in (245, 241, 242, 8114, 8115):
        return ValidationFailed("Data conversion or overflow error", [{"code": "type_mismatch"}])
    if err_num and err_num >= 50000:
        msg = clean_raiserror_message(err_str)
        return RuleViolation(msg)
    if err_num in (207, 208, 156, 8156, 1033, 102, 105):
        return ConfigError("Database configuration error")
    if err_num in (229, 230, 262, 300):
        return InternalError("Database permission error")

    if "HYT00" in sqlstate or "HYT01" in sqlstate or "Query timeout expired" in err_str:
        return QueryTimeout("Query timeout expired")
    if any(s in sqlstate for s in ("08001", "08S01", "08003", "28000")) or err_num in (53, 40613, 18456) or "Communication link failure" in err_str:
        return DbUnavailable("Database unavailable")

    return InternalError("An unexpected database error occurred")


def register_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", "unknown")
        headers = {}
        if exc.status_code == 503:
            headers["Retry-After"] = "5"
        headers["X-Request-Id"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "requestId": request_id,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        details = []
        for err in exc.errors():
            loc_list = err.get("loc", [])
            loc = ".".join(str(l) for l in loc_list)
            field = str(loc_list[-1]) if loc_list else ""
            err_type = err.get("type", "")
            code = "type_mismatch"
            if "missing" in err_type:
                code = "required"
            elif "too_long" in err_type or "max_length" in err_type:
                code = "too_long"
            elif "range" in err_type or "greater_than" in err_type:
                code = "out_of_range"
            details.append({
                "path": loc,
                "field": field,
                "code": code,
                "problem": err.get("msg", "Invalid value"),
            })
        return JSONResponse(
            status_code=422,
            headers={"X-Request-Id": request_id},
            content={
                "error": {
                    "code": "validation_failed",
                    "message": "Validation failed",
                    "requestId": request_id,
                    "details": details,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "unknown")
        status_code = exc.status_code
        code = "bad_request"
        if status_code == 404:
            code = "not_found"
        elif status_code == 405:
            code = "method_not_allowed"
        elif status_code in (401, 403):
            code = "unauthorized" if status_code == 401 else "forbidden"
        
        return JSONResponse(
            status_code=status_code,
            headers={"X-Request-Id": request_id},
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "requestId": request_id,
                    "details": [],
                }
            },
        )

    @app.exception_handler(DBAPIError)
    async def db_api_error_handler(request: Request, exc: DBAPIError):
        request_id = getattr(request.state, "request_id", "unknown")
        app_err = map_db_error(exc)
        headers = {"X-Request-Id": request_id}
        if app_err.status_code == 503:
            headers["Retry-After"] = "5"
        return JSONResponse(
            status_code=app_err.status_code,
            headers=headers,
            content={
                "error": {
                    "code": app_err.code,
                    "message": app_err.message,
                    "requestId": request_id,
                    "details": app_err.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=500,
            headers={"X-Request-Id": request_id},
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                    "requestId": request_id,
                    "details": [],
                }
            },
        )

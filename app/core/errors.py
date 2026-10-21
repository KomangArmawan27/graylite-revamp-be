from typing import Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[list[dict[str, Any]]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(message)

def register_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
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
            loc = ".".join(str(l) for l in err.get("loc", []))
            details.append({"field": loc, "problem": err.get("msg", "Invalid value")})
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_failed",
                    "message": "Invalid payload or parameters",
                    "requestId": request_id,
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        # Log exception with request_id here
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred",
                    "requestId": request_id,
                    "details": [],
                }
            },
        )

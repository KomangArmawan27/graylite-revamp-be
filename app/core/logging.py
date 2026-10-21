import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("erp-api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.time()
        
        response: Response = await call_next(request)
        
        duration = time.time() - start_time
        response.headers["X-Request-Id"] = request_id
        
        user_id = getattr(request.state, "user_id", "-")
        logger.info(f"req_id={request_id} user_id={user_id} method={request.method} path={request.url.path} status={response.status_code} duration={duration:.3f}s")
        return response

import time
import uuid
import re
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("erp-api")

REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        inbound_id = request.headers.get("X-Request-Id")
        if inbound_id and REQUEST_ID_REGEX.match(inbound_id):
            request_id = inbound_id
        else:
            request_id = uuid.uuid4().hex

        request.state.request_id = request_id
        start_time = time.time()
        
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Let exception handlers handle it, but we can ensure header
            raise exc

        duration = time.time() - start_time
        response.headers["X-Request-Id"] = request_id
        
        user_id = getattr(request.state, "user_id", "-")
        logger.info(f"req_id={request_id} user_id={user_id} method={request.method} path={request.url.path} status={response.status_code} duration={duration:.3f}s")
        return response

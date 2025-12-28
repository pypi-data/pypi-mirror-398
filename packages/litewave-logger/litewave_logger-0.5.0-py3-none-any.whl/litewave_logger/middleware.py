import uuid
import time
import logging
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from . import request_id_var, get_excluded_endpoints

logger = logging.getLogger(__name__)
RequestIdHeader = "X-Request-ID"
# This middleware is used to handle the request ID and provide comprehensive debugging.
# It checks for a 'X-Request-ID' header in the incoming request.
# If the header is present, its value is used as the request ID.
# If not, a new UUID is generated.
# The request ID is then stored in a context variable.
class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to handle the request ID and provide comprehensive debugging.
    It checks for a 'X-Request-ID' header in the incoming request.
    If the header is present, its value is used as the request ID.
    If not, a new UUID is generated.
    The request ID is then stored in a context variable.
    Provides detailed logging for incoming requests and outgoing responses.
    """
    async def dispatch(self, request: Request, call_next):
        # Extract request information
        method = request.method
        path = request.url.path
        # Get or generate request ID
        request_id = request.headers.get(RequestIdHeader)
        if not request_id:
            request_id = str(uuid.uuid4())
            # Set the request ID in the request headers if not present
            request.scope["headers"].append((RequestIdHeader.lower().encode(), request_id.encode()))

        # Set request ID in context
        request_id_var.set(request_id)

        # Check if this endpoint should be excluded from logging
        excluded_endpoints = get_excluded_endpoints()
        should_log = path not in excluded_endpoints

        if should_log:
            logger.info("request received", extra={"method": method, "path": path})

        try:
            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[RequestIdHeader] = request_id

            # Log response details only if endpoint is not excluded
            if should_log:
                logger.info("response sent", extra={"status_code": response.status_code})

            return response

        except Exception as e:
            logger.error("request failed", extra={"method": method, "path": path, "error": str(e)})

            # Re-raise the exception
            raise

__all__ = ["RequestIdMiddleware"]

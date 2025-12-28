import logging
import json
import os
from contextvars import ContextVar

# Context variable to hold the request ID
# This is used to store the request ID in the context of the request
# The value of the request ID is set in the RequestIdMiddleware
# Magically, this is maintained across multiple requests without it getting mixed up.
request_id_var = ContextVar("request_id", default=None)

# List of endpoints that should not be logged
_excluded_endpoints = []


class RequestIdFilter(logging.Filter):
    """
    A logging filter that injects the request_id from the context variable into the log record.
    """
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

class JsonLogFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON with required fields.
    """
    def format(self, record):
        # Collect fields with fallback to None for path, method, and status_code
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
            "message": record.getMessage(),
            "status_code": getattr(record, "status_code", None),
            "error": getattr(record, "error", None),
        }
        return json.dumps(log_object)

def setup_logging(excluded_endpoints=[]):
    """
    Configures the logging for the application.
    Uses a JSON formatter and adds the RequestIdFilter.

    Args:
        excluded_endpoints: List of endpoint paths that should not be logged.
                          For example: ['/health', '/metrics']
                          Defaults to None (empty list).
    """
    global _excluded_endpoints

    _excluded_endpoints = excluded_endpoints

    logger = logging.getLogger()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Prevent adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonLogFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Add the filter to all handlers
    for h in logger.handlers:
        if not any(isinstance(f, RequestIdFilter) for f in h.filters):
            h.addFilter(RequestIdFilter())

    logger.info(f"Setting log level to {logging.getLevelName(logger.level)}, with excluded endpoints: {excluded_endpoints}")
    return logger

def get_excluded_endpoints():
    """
    Returns the list of excluded endpoints.
    """
    return _excluded_endpoints

__all__ = ["setup_logging", "request_id_var", "RequestIdFilter", "get_excluded_endpoints"]

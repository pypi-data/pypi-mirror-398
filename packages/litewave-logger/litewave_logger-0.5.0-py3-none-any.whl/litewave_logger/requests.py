import requests
from . import request_id_var
import logging

logger = logging.getLogger(__name__)

# This is used to patch the requests library to automatically inject the 'X-Request-ID' header
# into all outgoing requests.
# It is used to ensure that the request ID is propagated to the external services.
def patch_requests():
    """
    Patches the requests library to automatically inject the 'X-Request-ID' header
    into all outgoing requests.
    """
    # Get the original Session class
    original_session_class = requests.Session

    # Create a new Session class that inherits from the original
    class PatchedSession(original_session_class):
        def request(self, method, url, *args, **kwargs):
            request_id = request_id_var.get()
            if request_id:
                headers = kwargs.get("headers", {})
                headers["X-Request-ID"] = request_id
                kwargs["headers"] = headers
                logger.debug(f"Injecting request_id {request_id} into outgoing request to {url}")
            return super().request(method, url, *args, **kwargs)

    # Replace the original Session class with our patched version
    requests.Session = PatchedSession

__all__ = ["patch_requests"]

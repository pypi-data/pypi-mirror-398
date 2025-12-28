import uuid
from celery.signals import (
    task_prerun,
    task_postrun,
    before_task_publish,
    after_setup_task_logger
)
from . import request_id_var, RequestIdFilter
import logging

logger = logging.getLogger(__name__)

# This signal runs in the CLIENT process (e.g., FastAPI app)
# This is where we tap into the request ID.
# Set the header for tasks to use the request ID.
@before_task_publish.connect
def propagate_request_id_to_celery_header(sender=None, headers=None, body=None, **kwargs):
    """
    Celery signal handler executed before a task is published.
    It retrieves the request ID from the current context and injects it
    into the task's headers. This propagates the ID from the client to the worker.
    """
    request_id = request_id_var.get()
    if request_id:
        if headers is None:
            headers = {}
        headers['request_id'] = request_id
        logger.info(f"Injecting request_id {request_id} into Celery task headers.")

# This signal runs in the WORKER process
# check if header has request_id
# this works magically because, we are importing the request_id_var from the same module in the worker process.
@task_prerun.connect
def set_request_id_from_celery_header(sender, task_id, task, args, kwargs, **extras):
    """
    Celery signal handler executed before a task runs in the worker.
    It retrieves the request ID from the task's headers (if present)
    and sets it in the worker's context variable.
    """
    request_id = task.request.get('request_id')
    if request_id:
        request_id_var.set(request_id)
        logger.info(f"Set request_id {request_id} from Celery task {task.name} headers")
    else:
        # Generate a new one if it's a standalone task initiated not from a request
        request_id_var.set(str(uuid.uuid4()))

@after_setup_task_logger.connect
def setup_celery_logging(logger, **kwargs):
    """
    This function is connected to the `after_setup_task_logger` signal.
    It modifies the ROOT logger's handlers to ensure that all propagated
    logs (including those from Celery tasks) are formatted correctly
    with our custom request_id.
    """
    # Celery task logs propagate to the root logger. We need to modify
    # the handlers on the root logger.
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        # Check if we've already configured this handler to avoid duplicates
        if not any(isinstance(f, RequestIdFilter) for f in handler.filters):
            # 1. Add the filter to inject the request_id
            handler.addFilter(RequestIdFilter())
            
            # 2. Set our custom formatter to display the request_id
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
            )
            handler.setFormatter(formatter)


@task_postrun.connect
def clear_request_id_after_celery(sender, task_id, task, args, kwargs, retval, state, **extras):
    """
    Celery signal handler executed after a task completes.
    It clears the request ID from the context variable in the worker.
    """
    request_id_var.set(None)

__all__ = [
    "propagate_request_id_to_celery_header",
    "set_request_id_from_celery_header",
    "clear_request_id_after_celery",
    "setup_celery_logging" # Expose the new function
]

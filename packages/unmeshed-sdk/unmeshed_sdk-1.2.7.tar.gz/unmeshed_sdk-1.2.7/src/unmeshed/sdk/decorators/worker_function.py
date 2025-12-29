import inspect
from functools import wraps
from typing import List

def worker_function(name, worker_queue_names: List[str] = None, namespace="default", max_in_progress=10):
    if worker_queue_names is None:
        worker_queue_names = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # You can add logic here to handle the function's execution
            return func(*args, **kwargs)

        wrapper.__signature__ = inspect.signature(func)

        wrapper.worker_function_metadata = {
            "name": name,
            "worker_queue_names": worker_queue_names,
            "namespace": namespace,
            "max_in_progress": max_in_progress,
        }

        return wrapper

    return decorator

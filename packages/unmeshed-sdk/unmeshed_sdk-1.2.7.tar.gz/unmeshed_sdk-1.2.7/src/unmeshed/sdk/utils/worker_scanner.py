import importlib
import inspect
import os
from typing import Callable, Any

from ..apis.workers.worker import Worker
from ..logger_config import get_logger

logger = get_logger(__name__)

EXCLUDED_DIRS = {'.venv', 'venv', 'node_modules', '__pycache__'}

class WorkerScanner:

    @staticmethod
    def find_workers(base_dir: str) -> list[Worker]:
        workers = []

        if not base_dir or not os.path.isdir(base_dir):
            logger.error("Valid base directory must be provided.")
            return workers

        for dirpath, dirnames, filenames in os.walk(base_dir):
            # Remove/skip any directories we want to exclude by mutating dirnames
            # so os.walk won't descend into them.
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDED_DIRS and not d.startswith('.')  # optional: skip hidden dirs
            ]

            # If dirpath itself is in an excluded path, skip processing files here
            # (If the directory name is in the path components)
            if any(part in EXCLUDED_DIRS for part in dirpath.split(os.sep)):
                continue

            for filename in filenames:
                # Skip non-Python or special files
                if (not filename.endswith('.py')
                        or filename.startswith('__')
                        or filename == "__init__.py"
                        or filename.startswith('_')
                        or filename.startswith('.')):
                    continue

                module_name = os.path.splitext(filename)[0]
                package_name = os.path.relpath(dirpath, base_dir).replace(os.sep, '.')
                # If package_name is just '.', it means dirpath == base_dir
                full_module_name = (f"{package_name}.{module_name}"
                                    if package_name != '.'
                                    else module_name)

                try:
                    logger.debug(f"Importing module: {full_module_name}")
                    module = importlib.import_module(full_module_name)
                    workers.extend(WorkerScanner.extract_callable_functions(module))

                except ImportError as e:
                    logger.error(f"ImportError for module '{full_module_name}': {str(e)}")
                except Exception as e:
                    logger.error(f"Error importing module '{full_module_name}': {str(e)}")

        if not workers:
            logger.info("No worker functions found in the specified directory.")

        return workers

    @staticmethod
    def extract_callable_functions(module) -> list[Worker]:
        """Extract worker functions and classes from a given module."""
        workers = []

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and hasattr(obj, 'worker_function_metadata'):
                metadata = obj.worker_function_metadata
                base_name = metadata["name"]
                worker_queue_names = metadata["worker_queue_names"]  # May be used if needed
                namespace = metadata["namespace"]
                max_in_progress = metadata["max_in_progress"]

                # noinspection DuplicatedCode
                if worker_queue_names and isinstance(worker_queue_names, list) and len(worker_queue_names) > 0:
                    for queue_name in worker_queue_names:
                        worker_instance = Worker(
                            execution_method=obj,
                            name=queue_name,
                            namespace=namespace,
                            max_in_progress=max_in_progress
                        )
                        workers.append(worker_instance)
                else:
                    worker_instance = Worker(
                        execution_method=obj,
                        name=base_name,
                        namespace=namespace,
                        max_in_progress=max_in_progress
                    )
                    workers.append(worker_instance)

            elif inspect.isclass(obj):  # Check if it's a class type
                if WorkerScanner.__is_instantiable(obj):
                    class_instance = obj()

                    for func_name in dir(class_instance):
                        method = getattr(class_instance, func_name)
                        if callable(method) and hasattr(method, 'worker_function_metadata'):
                            metadata = method.worker_function_metadata
                            base_name = metadata["name"]
                            worker_queue_names = metadata["worker_queue_names"]
                            namespace = metadata["namespace"]
                            max_in_progress = metadata["max_in_progress"]
                            bound_method: Callable[..., Any] = method.__get__(class_instance) # type: ignore

                            # noinspection DuplicatedCode
                            if worker_queue_names and isinstance(worker_queue_names, list) and len(worker_queue_names) > 0:
                                for queue_name in worker_queue_names:
                                    worker_instance = Worker(
                                        execution_method=bound_method,
                                        name=queue_name,
                                        namespace=namespace,
                                        max_in_progress=max_in_progress
                                    )
                                    workers.append(worker_instance)
                            else:
                                worker_instance = Worker(
                                    execution_method=bound_method,
                                    name=base_name,
                                    namespace=namespace,
                                    max_in_progress=max_in_progress
                                )
                                workers.append(worker_instance)

        return workers

    @staticmethod
    def __is_instantiable(cls: type) -> bool:
        try:
            cls()
            return True
        except TypeError as e:
            logger.debug(f"Cannot instantiate {cls.__name__}: {e}")
            return False

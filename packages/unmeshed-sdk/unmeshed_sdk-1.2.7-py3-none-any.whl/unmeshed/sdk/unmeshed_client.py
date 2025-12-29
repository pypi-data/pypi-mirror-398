import asyncio
import atexit
import inspect
import json
import logging
import os
import random
import threading
import time
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
import socket
from typing import Type, get_origin, Union, Any, Optional

from .apis.http.http_client_factory import HttpClientFactory
from .apis.http.http_request_factory import HttpRequestFactory
from .apis.poller.poller_client import PollerClient
from .apis.process.process_client import ProcessClient
from .apis.registration.registration_client import RegistrationClient
from .apis.submit.submit_client import SubmitClient
from .apis.submit.work_response_builder import WorkResponseBuilder
from .apis.workers.worker import Worker
from .common.api_call_type import ApiCallType
from .common.process_action_response_data import ProcessActionResponseData
from .common.process_data import ProcessData
from .common.process_definition import ProcessDefinition
from .common.process_request_data import ProcessRequestData
from .common.process_search_request import ProcessSearchRequest
from .common.step_data import StepData
from .common.step_queue_poll_state import StepQueuePollState
from .common.step_size import StepSize, StepQueueNameData
from .common.unmeshed_constants import StepType
from .common.work_request import WorkRequest
from .configs.client_config import ClientConfig
from .logger_config import LoggerFactory, get_logger
from .schedulers.step_result import StepResult
from .utils.worker_scanner import WorkerScanner

LoggerFactory.setup_logging(os.getenv("enable_file_logging") == "true")
logger = get_logger(__name__)


class UnmeshedClient:
    __thread_local = threading.local()

    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config
        self.worker_to_name_mapping = dict()
        self.worker_is_co_routine = dict()

        self.__stop_polling = False
        self.__polling_error_reported = False
        self.__poll_retry_count = 1
        self.__executing_count = 0
        self.__last_printed_running = 0
        self.__last_printed_polling = 0

        if not self.client_config.get_client_id() or not self.client_config.has_token():
            raise ValueError("Cannot initialize without a valid clientId and token")

        self.__http_client_factory = HttpClientFactory(client_config)
        self.__http_request_factory = HttpRequestFactory(client_config)

        self.__poll_states: dict[str, 'StepQueuePollState'] = dict()

        self.__executor = ThreadPoolExecutor(max_workers=max(10, client_config.get_max_threads_count()))

        self.__registration_client = RegistrationClient(client_config, self.__http_client_factory,
                                                        self.__http_request_factory)
        self.__submit_client = SubmitClient(self.__http_client_factory, self.__http_request_factory, client_config)
        self.__poller_client = PollerClient(client_config, UnmeshedClient.get_host_name(), self.__http_client_factory, self.__http_request_factory)

        self.__process_client = ProcessClient(self.__http_client_factory, self.__http_request_factory, client_config)

        self.__work_response_builder = WorkResponseBuilder()
        atexit.register(self.__executor.shutdown, wait=False)

    def create_new_process_definition(self, process_definition: ProcessDefinition) -> ProcessDefinition:
        return self.__process_client.create_new_process_definition(process_definition=process_definition)

    def update_process_definition(self, process_definition: ProcessDefinition) -> ProcessDefinition:
        return self.__process_client.update_process_definition(process_definition=process_definition)

    def delete_process_definitions(self, process_definitions : list[ProcessDefinition], version_only : bool) -> Any:
        return self.__process_client.delete_process_definitions(process_definitions=process_definitions, version_only=version_only)

    def get_all_process_definitions(self) -> list[ProcessDefinition]:
        return self.__process_client.get_all_process_definitions()

    def get_process_definition_latest_or_version(self, namespace : str, name : str, version : Optional[int]) -> ProcessDefinition:
        return self.__process_client.get_process_definition_latest_or_version(namespace=namespace, name=name, version=version)

    def get_process_definition_versions(self, namespace:str, name:str) -> list[int]:
        return self.__process_client.get_process_definition_versions(namespace=namespace, name=name)

    def run_process_sync(self, process_request_data: ProcessRequestData,
                         http_read_timeout: int = 10,  # Timeout for the HTTP request
                         process_timeout_seconds: int = None  # Process timeout
                         ) -> ProcessData:
        return self.__process_client.run_process_sync(process_request_data, http_read_timeout = http_read_timeout, process_timeout_seconds = process_timeout_seconds)

    def run_process_async(self, process_request_data: ProcessRequestData) -> ProcessData:
        return self.__process_client.run_process_async(process_request_data)

    def get_process_data(self, process_id: int, include_steps: bool = False) -> ProcessData:
        return self.__process_client.get_process_data(process_id, include_steps)

    def get_step_data(self, step_id: int) -> StepData:
        return self.__process_client.get_step_data(step_id)

    def search_process_executions(self, params: ProcessSearchRequest) -> list['ProcessData']:
        return self.__process_client.search_process_executions(params)

    def invoke_api_mapping_get(self, endpoint: str = None, _id: str = None, correlation_id: str = None, api_call_type: ApiCallType = None) -> dict['str', 'Any']:
        return self.__process_client.invoke_api_mapping_get(endpoint, _id, correlation_id, api_call_type)

    def invoke_api_mapping_post(self, endpoint: str = None, _input: dict['str', 'Any'] = None, _id: str = None, correlation_id: str = None, api_call_type: ApiCallType = None) -> dict['str', 'Any']:
        return self.__process_client.invoke_api_mapping_post(endpoint, _input, _id, correlation_id, api_call_type)

    def bulk_terminate(self,  process_ids: list['int'], reason: str = None) -> ProcessActionResponseData:
        return self.__process_client.bulk_terminate(process_ids, reason)

    def bulk_resume(self, process_ids: list['int']) -> ProcessActionResponseData:
        return self.__process_client.bulk_resume(process_ids)

    def bulk_reviewed(self,  process_ids: list['int'], reason: str = None) -> ProcessActionResponseData:
        return self.__process_client.bulk_reviewed(process_ids, reason)

    def rerun(self, process_id: int, version: int = None) -> ProcessData:
        return self.__process_client.rerun(process_id, version)

    def register_decorated_workers(self, scan_path: str):
        workers_to_scan: list = WorkerScanner.find_workers(scan_path)
        logger.info(f"Found {len(workers_to_scan)} workers from scan path {scan_path}")
        for worker in workers_to_scan:
            self.register_worker(worker)
        logger.info(f"Registered {len(workers_to_scan)} workers from scan path {scan_path}")

    def register_worker(self, worker: Worker = None, worker_queue_names: list[str] = None):
        if worker is None:
            return
        if worker_queue_names and len(worker_queue_names) > 0:
            for queue_name in worker_queue_names:
                w = Worker(execution_method=worker.execution_method,
                           name=queue_name,
                           namespace=worker.namespace,
                           max_in_progress=worker.max_in_progress
                           )
                self.__register_worker(w)
        else:
            self.__register_worker(worker)

    def __register_worker(self, worker: Worker):
        # Create unique worker_id using namespace and name
        worker_id = self.__formatted_worker_id(worker.namespace, worker.name)

        if worker_id in self.worker_to_name_mapping:
            raise ValueError(
                f"Worker with namespace '{worker.namespace}' and name '{worker.name}' is already registered.")

        if not worker.execution_method:
            raise ValueError(f"No execution method found for worker {worker.name} in namespace {worker.namespace}.")

        self.worker_to_name_mapping[worker_id] = worker
        is_coroutine_function = inspect.iscoroutinefunction(worker.execution_method)
        self.worker_is_co_routine[worker_id] = is_coroutine_function
        if is_coroutine_function:
            logger.info(
                f"Worker {worker.namespace}:{worker.name} has an async method which will be run as a coroutine.")
        method = worker.execution_method
        sig = inspect.signature(method)
        params = sig.parameters

        if len(params) != 1:
            raise ValueError(
                f"Execution method {method.__name__} must have exactly one parameter, but found {len(params)}.")

        self.__registration_client.add_workers([worker])

    @staticmethod
    def __formatted_worker_id(namespace: str, name: str) -> str:
        return f"{namespace}:-#-:{name}"

    async def __async_task_processing(self):
        loop = asyncio.get_running_loop()
        last_log_time = 0
        while not self.__stop_polling:
            try:
                tasks = []
                # noinspection PyTypeChecker
                work_requests = await loop.run_in_executor(self.__executor, self.__poll_for_work)

                self.__poll_retry_count = 1  # reset poll retry after success

                if work_requests:
                    for work_request in work_requests:
                        worker_id = self.__formatted_worker_id(work_request.get_step_namespace(),
                                                               work_request.get_step_name())
                        worker = None
                        if worker_id in self.worker_to_name_mapping:
                            worker = self.worker_to_name_mapping[worker_id]
                        if worker:
                            if self.worker_is_co_routine[worker_id]:
                                task = asyncio.create_task(self.__run_async_step(worker, work_request))
                            else:
                                task = loop.run_in_executor(self.__executor, self.__run_step, worker, work_request)
                            tasks.append(task)
                    logger.info("All tasks scheduled. Continuing the polling")

                poll_interval_millis_ = self.client_config.poll_interval_millis / 1000
                time.sleep(poll_interval_millis_)

                # Check if at least 10 seconds have passed since last log
                if time.time() - last_log_time >= 60:
                    logging.info("Poll interval is %s ms", poll_interval_millis_ * 1000)
                    last_log_time = time.time()  # Update the last log time
            except Exception as ex:
                seconds = min(20.0, random.uniform(0.1, 1.0) * self.__poll_retry_count)
                logging.error("An error occurred during polling, will continue after %s seconds : %s", seconds, ex)
                self.__poll_retry_count += 1
                time.sleep(seconds)

    def start(self):
        if not self.client_config.has_token():
            raise RuntimeError(
                "Credentials not configured correctly. Client configuration requires auth client id and token to be set.")

        if self.__registration_client.get_workers() is None or len(self.__registration_client.get_workers()) == 0:
            logger.error("No workers configured. Will not poll for any work.")
            return

        if not self.client_config.is_enable_results_submission():
            logger.warning("Batch processing is disabled for results submission")
            return

        for worker in self.__registration_client.get_workers():
            default_max_size = worker.max_in_progress
            worker_id = self.__formatted_worker_id(worker.namespace, worker.name)
            self.__poll_states[worker_id] = StepQueuePollState(default_max_size)

        logger.info("Registering %s workers", len(self.__registration_client.get_workers()))
        self.__registration_client.renew_registration()

        logger.info("Unmeshed Python SDK starting to poll")

        asyncio.run(self.__async_task_processing())

    def __poll_for_work(self):
        workers = self.__registration_client.get_workers()
        worker_tasks = []
        worker_request_count = defaultdict(int)
        for worker in workers:
            step_queue_name_data = StepQueueNameData(orgId=0, namespace=worker.namespace, stepType=StepType.WORKER, name=worker.name)
            worker_id = self.__formatted_worker_id(worker.namespace, worker.name)

            if worker_id not in self.__poll_states:
                raise RuntimeError(f"Unexpected missing poll state for worker: {worker_id}")

            size = self.__poll_states[worker_id].acquire_max_available()
            worker_request_count[worker_id] = size
            if size > 0:
                worker_task = StepSize(step_queue_name_data, size)
                worker_tasks.append(worker_task)

        if len(worker_tasks) == 0:
            return

        if time.time() - self.__last_printed_polling > 10:  # 10 Seconds
            logger.info("Tasks being polled: %s", worker_tasks)
            self.__last_printed_polling = time.time()

        try:
            work_requests: list[WorkRequest] = self.__poller_client.poll(worker_tasks)
        except Exception as ex:
            self.release_unused_permits(defaultdict(int), worker_request_count)
            raise ex

        if len(work_requests) > 0:
            logger.info("Received work requests : %s", len(work_requests))

        worker_received_count = defaultdict(int)
        for work_request in work_requests:
            self.__executing_count = self.__executing_count + 1
            worker_id = self.__formatted_worker_id(work_request.get_step_namespace(), work_request.get_step_name())
            worker_received_count[worker_id] += 1

        self.release_unused_permits(worker_received_count, worker_request_count)

        if time.time() - self.__last_printed_running > 2:  # 10 Seconds
            log_entries = []
            for s in self.__registration_client.get_workers():
                worker_id: str = self.__formatted_worker_id(s.namespace, s.name)
                poll_state = self.__poll_states[worker_id]
                available = poll_state.max_available()
                total = poll_state.total_count
                log_entries.append(
                    f"{s.namespace}:{s.name} = Available[{available}] / [{worker_request_count.get(worker_id, 0)}] / [{total}]")

            log = ", ".join(log_entries)

            logger.info(
                f"Running : {self.__executing_count} st: {self.__submit_client.get_submit_tracker_size()} t: {self.__executing_count + self.__submit_client.get_submit_tracker_size()} - permits {log}")

            self.__last_printed_running = time.time()

        return work_requests

    def release_unused_permits(self, worker_received_count, worker_request_count):
        for worker_id, requested_count in worker_request_count.items():
            if worker_id in self.__poll_states:
                self.__poll_states[worker_id].release(requested_count - worker_received_count.get(worker_id, 0))

    def stop(self):
        """Gracefully stop the polling loop and shutdown the executor."""
        self.__stop_polling = True
        logger.info("Stopping the executor pool")
        self.__executor.shutdown(wait=True)
        self.__submit_client.stop()
        logger.info("Stopped the executor pool")

    @classmethod
    def set_current_work_request(cls, work_request):
        cls.__thread_local.current_work_request = work_request

    @classmethod
    def get_current_work_request(cls):
        return getattr(cls.__thread_local, "current_work_request", None)

    def __run_step(self, worker: Worker, work_request: WorkRequest) -> None:
        method = worker.execution_method
        sig = inspect.signature(method)
        params = sig.parameters

        param_name, param = next(iter(params.items()))
        expected_type: Type = param.annotation

        input_param = work_request.get_input_param()
        try:
            input_param = self.__convert_input_param(input_param, expected_type)
            UnmeshedClient.set_current_work_request(work_request)
            result = method(input_param)
            step_result = None
            if isinstance(result, StepResult):
                step_result = result
            else:
                step_result = StepResult(result=result if result is not None else dict())

            self.__handle_work_completion(work_request, step_result, None)

        except Exception as e:
            logger.exception("Error executing step for work request %s: %s", work_request, e)
            self.__handle_work_completion(work_request, StepResult("Failed"), e)

    async def __run_async_step(self, worker: Worker, work_request: WorkRequest) -> None:
        method = worker.execution_method
        sig = inspect.signature(method)
        params = sig.parameters

        param_name, param = next(iter(params.items()))
        expected_type: Type = param.annotation

        input_param = work_request.get_input_param()
        try:
            input_param = self.__convert_input_param(input_param, expected_type)
            UnmeshedClient.__thread_local.current_work_request = work_request
            result = await method(input_param)

            step_result = None
            if isinstance(result, StepResult):
                step_result = result
            else:
                step_result = StepResult(result=result if result is not None else dict())

            self.__handle_work_completion(work_request, step_result, None)

        except Exception as e:
            logger.error("Error executing step for work request %s: %s", work_request, e)
            self.__handle_work_completion(work_request, StepResult("Failed"), e)

    def __handle_work_completion(self, work_request: WorkRequest, step_result: StepResult,
                                 throwable: Union[Exception, None] = None):
        try:
            # Determine whether to generate a success or failure response
            if throwable:
                work_response = self.__work_response_builder.fail_response(work_request, throwable)
            elif step_result.keep_running == True and step_result.reschedule_after_seconds > 0:
                work_response = self.__work_response_builder.running_response(work_request, step_result)
            else:
                work_response = self.__work_response_builder.success_response(work_request, step_result)

            # Format the step ID
            step_id = self.__formatted_worker_id(work_request.get_step_namespace(), work_request.get_step_name())

            # Submit the work response
            self.__submit_client.submit(work_response, self.__poll_states[step_id])
            self.__executing_count -= 1

            logger.debug("Work Response: %s", work_response)

        except Exception as e:
            logger.exception("Error in __handle_work_completion: %s", e)  # Logs full stack trace
            raise  # Re-raise the exception to propagate the error

    @staticmethod
    def __convert_input_param(input_param, expected_type: Type):
        origin_type = get_origin(expected_type)
        if origin_type:
            if isinstance(input_param, dict) and origin_type is dict:
                return expected_type(**input_param)  # Convert dictionary to expected type (if dataclass)
            elif not isinstance(input_param, expected_type):
                raise TypeError(f"Expected parameter of type {expected_type}, but got {type(input_param)}")

        if isinstance(input_param, expected_type):
            return input_param

        if expected_type is dict and isinstance(input_param, str):
            try:
                return json.loads(input_param)  # Safer than eval()
            except json.JSONDecodeError:
                raise TypeError(f"Invalid dictionary string: {input_param}")

        try:
            return expected_type(input_param)
        except (ValueError, TypeError) as e:
            raise TypeError(f"Cannot convert {input_param} to {expected_type}: {e}")

    @staticmethod
    def get_host_name():
        unmeshed_host_name = os.getenv("UNMESHED_HOST_NAME")
        if unmeshed_host_name and unmeshed_host_name.strip():
            return unmeshed_host_name.strip()

        # Linux, macOS
        hostname = os.getenv("HOSTNAME")
        if hostname and hostname.strip():
            return hostname.strip()

        # Windows
        hostname = os.getenv("COMPUTERNAME")
        if hostname and hostname.strip():
            return hostname.strip()

        # Java fallback
        try:
            hostname = socket.gethostname()
            if hostname and hostname.strip():
                return hostname.strip()
        except Exception:
            pass

        return "-"
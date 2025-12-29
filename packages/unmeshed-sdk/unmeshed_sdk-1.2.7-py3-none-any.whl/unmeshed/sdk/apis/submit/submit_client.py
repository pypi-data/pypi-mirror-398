import atexit
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

from ..http.http_client_factory import HttpClientFactory
from ..http.http_request_factory import HttpRequestFactory
from ...common.client_submit_result import ClientSubmitResult
from ...common.step_queue_poll_state import StepQueuePollState
from ...common.work_response import WorkResponse
from ...common.work_response_tracker import WorkResponseTracker
from ...configs.client_config import ClientConfig
from ...logger_config import get_logger

logger = get_logger(__name__)

class SubmitClient:
    CLIENTS_RESULTS_URL = "api/clients/bulkResults"

    def __init__(self, http_client_factory: HttpClientFactory, http_request_factory: HttpRequestFactory, client_config: ClientConfig):
        self.http_client = http_client_factory.create()
        self.http_request_factory = http_request_factory
        self.client_config = client_config
        self.timeoutSeconds = client_config.get_submit_client_poll_timeout_seconds()
        self.__stop_polling = False

        if not self.client_config.get_client_id():
            raise ValueError("Cannot submit results without a clientId")

        if not self.client_config.is_enable_results_submission():
            logger.warning("Batch processing is disabled for results submission")
            return

        self.__main_queue = Queue(maxsize=100000)
        self.__retry_queue = Queue(maxsize=100000)
        self.__submit_tracker : dict[int, WorkResponseTracker] = {}
        self.__submit_tracker_lock = threading.Lock()

        if os.getenv("DISABLE_SUBMIT_CLIENT", "false").lower() != "true":
            self.__executor = ThreadPoolExecutor(max_workers=3)
            self.__executor.submit(self.__cleanup_lingering_submit_trackers)
            self.__executor.submit(self.__process_queue, self.__main_queue, "main")
            self.__executor.submit(self.__process_queue, self.__retry_queue, "retry")
            atexit.register(self.__executor.shutdown, wait=False)
        else:
            self.__executor = None


    def stop(self):
        self.__stop_polling = True
        if self.__executor:
            logger.info("Stopping the submit executor pool")
            self.__executor.shutdown(wait=True)
            logger.info("Stopped the submit executor pool")

    def __cleanup_lingering_submit_trackers(self):
        while not self.__stop_polling:
            counter = 0
            current_millis = time.time_ns() / 1_000_000

            with self.__submit_tracker_lock:
                step_ids = list(self.__submit_tracker.keys())
                for step_id in step_ids:
                    tracker = self.__submit_tracker.get(step_id)
                    if isinstance(tracker, WorkResponseTracker):
                        seconds = 10 * 60
                        remove_eligible = current_millis - tracker.queued_time > (seconds * 1000)
                        if remove_eligible:
                            tracker.step_poll_state.release(1)
                            counter += 1
                            del self.__submit_tracker[step_id]

            time.sleep(3)

    def __process_queue(self, queue, queue_type: str):
        while not self.__stop_polling:
            try:
                try:
                    first_item = queue.get(timeout=self.timeoutSeconds)
                except Empty:
                    if not self.__stop_polling:
                        logging.info(f"No item received from queue {queue_type} in {self.timeoutSeconds} seconds, retrying...")
                    continue

                batch = [first_item]

                for _ in range(self.client_config.get_response_submit_batch_size() - 1):
                    try:
                        batch.append(queue.get_nowait())
                    except Empty:
                        break

                json_body = [
                    {
                        "processId": response.get_process_id(),
                        "stepId": response.get_step_id(),
                        "startedAt": response.get_started_at(),
                        "stepExecutionId": response.get_step_execution_id(),
                        "output": response.get_output(),
                        "status": response.get_status(),
                        "rescheduleAfterSeconds": response.get_reschedule_after_seconds()
                    }
                    for response in batch
                ]
                params = {}

                try:
                    response = self.http_request_factory.create_post_request(
                        self.CLIENTS_RESULTS_URL, params=params, body=json_body
                    )
                except Exception as e:
                    time.sleep(3)
                    logging.error(f"Bulk request failed for batch. Re-queuing all items. Error: {str(e)}")
                    for work_response in batch:
                        self.__handle_all_request_failure(work_response, str(e))
                    continue

                logging.debug(f"Bulk request response: {response.status_code}")

                if response.status_code != 200:
                    logging.error(f"Bulk request failed with status {response.status_code}. Re-queuing all items.")
                    for work_response in batch:
                        self.__handle_all_request_failure(work_response, "Response status not 200")
                    continue

                response_map = json.loads(response.text)
                logging.info(f"Bulk request response size: {len(response_map)}")

                for work_response in batch:
                    result = response_map.get(str(work_response.get_step_id()))
                    with self.__submit_tracker_lock:
                        work_response_tracker = self.__submit_tracker.get(work_response.get_step_id())

                    if not result or result.get("error_message"):
                        error_message = result.get("error_message", "No result") if result else "No result"
                        logging.error(
                            f"Error for WorkResponse {work_response.get_process_id()} {work_response.get_step_id()}: {error_message}"
                        )
                        self.__enqueue_for_retry(work_response, result, work_response_tracker)
                    else:
                        logging.info(f"Result from stepId {work_response.get_process_id()} {work_response.get_step_id()} submitted!")
                        with self.__submit_tracker_lock:
                            self.__submit_tracker.pop(work_response.get_step_id(), None)
                        if work_response_tracker:
                            work_response_tracker.step_poll_state.release(1)
            except Exception as e:
                logging.exception("Exception occurred while processing queue item in submit: %s %s", queue_type, e)
                continue

    def __handle_all_request_failure(self, work_response: WorkResponse, message):
        with self.__submit_tracker_lock:
            work_response_tracker = self.__submit_tracker.get(work_response.get_step_id())

        if work_response_tracker:
            self.__enqueue_for_retry(work_response, ClientSubmitResult(work_response.get_process_id(), work_response.get_step_id(), message, 400), work_response_tracker)

    def __enqueue_for_retry(self, work_response: WorkResponse, result, work_response_tracker: WorkResponseTracker):
        if self.__is_permanent_error__(result.errorMessage):
            logging.error(f"Permanent error for WorkResponse {work_response.get_process_id()}: {result.errorMessage}")
            with self.__submit_tracker_lock:
                self.__submit_tracker.pop(work_response.get_step_id(), None)
            work_response_tracker.step_poll_state.release(1)
            return

        count = work_response_tracker.retry_count + 1
        if count > self.client_config.get_max_submit_attempts():
            logging.error(f"Max retry attempts reached for WorkResponse {work_response.get_step_id()} - {work_response.get_process_id()}")
            with self.__submit_tracker_lock:
                self.__submit_tracker.pop(work_response.get_step_id(), None)
            work_response_tracker.step_poll_state.release(1)
            return

        work_response_tracker.retry_count = count
        self.__retry_queue.put(work_response)
        logging.debug(f"Re-queued WorkResponse {work_response.get_process_id()} for retry attempt {count}")

    def __is_permanent_error__(self, error_message):
        if not error_message:
            return False
        for keyword in self.client_config.permanent_error_keywords:
            if keyword in error_message:
                return True
        return False

    def submit(self, work_response: WorkResponse, step_poll_state: StepQueuePollState):
        logger.debug(f"Submitting results to queue: {work_response}")
        with self.__submit_tracker_lock:
            epoch_millis = time.time_ns() / 1_000_000
            self.__submit_tracker[work_response.get_step_id()] = WorkResponseTracker(work_response, 0, epoch_millis, step_poll_state)
            self.__main_queue.put(work_response)
            logger.debug(f"Result[{work_response.get_status()}] from stepId {work_response.get_step_id()} queued!")

    def get_submit_tracker_size(self) -> int:
        with self.__submit_tracker_lock:
            return len(self.__submit_tracker)

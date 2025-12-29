import asyncio
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict

from src.unmeshed.sdk.apis.workers.worker import Worker
from src.unmeshed.sdk.configs.client_config import ClientConfig
from src.unmeshed.sdk.decorators.worker_function import worker_function
from unmeshed.sdk.common.api_call_type import ApiCallType
from unmeshed.sdk.common.process_data import ProcessData
from unmeshed.sdk.common.process_request_data import ProcessRequestData
from unmeshed.sdk.common.process_search_request import ProcessSearchRequest
from unmeshed.sdk.schedulers.step_result import StepResult
from unmeshed.sdk.unmeshed_client import UnmeshedClient
from unmeshed.sdk.utils.worker_scanner import logger


@dataclass
class SampleResponse:
    success: bool = False
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self) # type: ignore


@worker_function(name="worker3_alt", max_in_progress=500)
def task_hello_world1(input_dict: dict) -> dict:
    # print(f"Received input: {input_dict}")
    output_dict = {
        "message": "Hello, world!",
        "input_received": input_dict
    }
    return output_dict

def sample_function(input_dict: dict) -> dict:
    output_dict = {
        "message": "Hello, world! sample_function",
        "input_received": input_dict
    }
    return output_dict

async def sample_async_function(input_dict: dict) -> dict:
    output_dict = {
        "message": "Hello, world! sample_async_function",
        "input_received": input_dict
    }
    return output_dict


async def task_hello_world2(input_dict: dict) -> dict:
    # print(f"Received input from task_hello_world2: {input_dict}")
    output_dict = {
        "message": "Hello, world! task_hello_world2",
        "input_received": input_dict
    }
    return output_dict


def waiting_function(input_dict: dict) -> dict:
    # print(f"Received input from waiting_function: {input_dict}")
    time.sleep(0.2)
    output_dict = {
        "message": "Hello, world! waiting_function",
        "input_received": input_dict
    }
    return output_dict


async def async_waiting_function(input_dict: dict) -> dict:
    # print(f"Received input from waiting_function: {input_dict}")
    await asyncio.sleep(0.5)
    output_dict = {
        "message": "Hello, world! async waiting_function",
        "input_received": input_dict
    }
    return output_dict


# noinspection PyUnusedLocal
@worker_function(name="list_no_test", max_in_progress=100, namespace="testns3", worker_queue_names=["res_list", "res_list2"])
def list_no_test(inp: dict) -> list:
    # Define a complex list with nested arrays and objects
    lst = [
        "23232",
        {
            "id": "1",
            "name": "Item 1",
            "tags": ["tag1", "tag2"],
            "details": {
                "description": "This is a description for item 1",
                "attributes": [100, 200, 300]
            }
        },
        {
            "id": "2",
            "name": "Item 2",
            "tags": ["tag3", "tag4"],
            "details": {
                "description": "This is a description for item 2",
                "attributes": [400, 500, 600]
            }
        },
        {
            "id": "3",
            "name": "Item 3",
            "tags": ["tag5", "tag6"],
            "details": {
                "description": "This is a description for item 3",
                "attributes": [700, 800, 900]
            }
        }
    ]
    return lst

@worker_function(name="sample_annotated_worker", max_in_progress=100, namespace="default", worker_queue_names=["sample_annotated_worker_name1", "sample_annotated_worker_name2"])
def sample_annotated_worker(response: SampleResponse) -> SampleResponse:
    print(f"Processing response: {response.to_dict()}")
    return SampleResponse(
        success=True,
        message="Sample Annotated Worker",
        data={
            "original_response": response.to_dict(),
            "worker_note": "Processed by sample_annotated_worker"
        }
    )

@worker_function(name="task_second_worker", max_in_progress=100, namespace="testns3", worker_queue_names=["task_second_worker"])
def task_second_worker(response: SampleResponse) -> SampleResponse:
    print(f"Processing response: {response.to_dict()}")
    return SampleResponse(
        success=True,
        message="Second worker processed",
        data={
            "original_response": response.to_dict(),
            "worker_note": "Processed by secondary worker"
        }
    )


class NotestWorkerCallable:
    def __init__(self):
        pass

    @worker_function(name="class_worker", max_in_progress=5, namespace="testns3")
    def class_worker(self, worker_input: dict) -> dict:
        print("Input received is " + str(worker_input))
        return {
            "a": "bcd"
        }


class CustomError(RuntimeError):
    def __init__(self, message, error_code, error_data):
        super().__init__(message)
        self.error_code = error_code
        self.error_data = error_data


# noinspection PyUnusedLocal
def exception_step(input_dict: dict) -> dict:
    """Raises a custom exception with sample error details"""
    raise CustomError(
        "Intentional exception from exception_step",
        error_code="CUSTOM_ERROR_123",
        error_data={"step": 2, "status": "failed"}
    )

def test_worker_3(input_dict: dict) -> StepResult:
    print("Running reschedule worker")

    return StepResult(
        result={"message": "Hello world !!"},
        keep_running=True,
        reschedule_after_seconds=6
    )


def main():
    client_config = ClientConfig()
    # port = os.getenv("UNMESHED_PORT")
    # client_config.set_client_id(os.getenv("UNMESHED_CLIENT_ID"))
    # client_config.set_auth_token(os.getenv("UNMESHED_AUTH_TOKEN"))
    # if port:
    #     client_config.set_port(int(port))
    # client_config.set_base_url(os.getenv("UNMESHED_URL"))

    client_config.set_client_id("26977084-83b0-43f8-98c9-21076d86393a")
    client_config.set_auth_token("s70frnUc3JB1orUqFI7r")
    client_config.set_port(8080)
    client_config.set_base_url("http://localhost")
    client_config.set_initial_delay_millis(50)
    client_config.set_step_timeout_millis(3600000)
    client_config.set_work_request_batch_size(200)
    client_config.set_response_submit_batch_size(1000)
    client_config.set_max_threads_count(10)
    client_config.set_poll_interval_millis(10)

    client = UnmeshedClient(client_config)

    worker1: Worker = Worker(task_hello_world2, "worker3")
    worker1.max_in_progress = 3000
    client.register_worker(worker1)

    worker2: Worker = Worker(task_hello_world2, "worker4")
    worker2.max_in_progress = 1000
    client.register_worker(worker2)

    worker3: Worker = Worker(async_waiting_function, "waiting_worker")
    worker3.max_in_progress = 10000
    client.register_worker(worker3)

    ## Register multiple queue names for the same worker
    worker5: Worker = Worker(execution_method=task_hello_world1, name="worker5", namespace="default", max_in_progress = 10)
    client.register_worker(worker5, worker_queue_names=["worker_queue_1", "worker_queue_2", "worker_queue_3"])

    reschedule_worker = Worker(execution_method= test_worker_3, name="test_worker_3", max_in_progress=5)
    client.register_worker(reschedule_worker)

    client.register_worker(
        Worker(execution_method=exception_step, name="exception_step", namespace="testns3", max_in_progress=100))

    current_directory_full_path = os.getcwd()
    client.register_decorated_workers(current_directory_full_path)
    client.start()

    process_request: ProcessRequestData = ProcessRequestData("default", "test_process", 1, "req001", "corr001", {
        "test1": "value",
        "test2": 100,
        "test3": 100.0,
    })
    process_data1: ProcessData = client.run_process_sync(process_request)
    logger.info(
        f"Sync execution of process request %s returned %s",
        process_request,
        process_data1.to_json()
    )

    process_data2: ProcessData = client.run_process_async(process_request)
    logger.info(
        f"Async execution of process request %s returned %s",
        process_request,
        process_data2.to_json()
    )

    process_data1_retrieved1: ProcessData = client.get_process_data(process_data1.processId)
    logger.info(
        f"Retrieving process %s returned %s",
        process_data1.processId,
        process_data1_retrieved1.to_json()
    )

    logger.info("Since the flag to include steps was false the steps was not returned: %s", len(process_data1_retrieved1.stepRecords))


    process_data1_retrieved2: ProcessData = client.get_process_data(process_data1.processId, include_steps=True)
    logger.info(
        f"Retrieving process %s returned %s",
        process_data1.processId,
        process_data1_retrieved2.to_json()
    )

    logger.info("Since the flag to include steps was true the steps was returned: %s", len(process_data1_retrieved2.stepRecords))

    step_data1 = client.get_step_data(process_data1_retrieved2.steps[0].get("id"))
    logger.info(
        f"Retrieving step data %s returned %s",
        step_data1.processId,
        step_data1.to_json()
    )

    process_search_request: ProcessSearchRequest = ProcessSearchRequest()
    process_search_request.names = ["test_process"]
    process_search_request.limit = 20
    process_search_request.namespace = "default"
    processes_search_results_data: list['ProcessData'] = client.search_process_executions(process_search_request)
    logger.info(
        f"Search returned %s", len(processes_search_results_data)
    )

    rerun_process_data = client.rerun(process_id=process_data1.processId, version=1)
    logger.info(
        f"Rerun of process %s returned %s",
        process_data1.processId,
        rerun_process_data.to_json()
    )

    action_response = client.bulk_terminate(process_ids=[process_data1.processId, 1, 2])
    logger.info(
        f"Bulk terminate of 3 process %s returned %s",
        process_data1.processId,
        action_response.details
    )

    action_response = client.bulk_resume(process_ids=[process_data1.processId, 1, 2])
    logger.info(
        f"Bulk resume of 3 process %s returned %s",
        process_data1.processId,
        action_response.details
    )

    action_response = client.bulk_reviewed(process_ids=[process_data1.processId, 1, 2])
    logger.info(
        f"Bulk review of 3 process %s returned %s",
        process_data1.processId,
        action_response.details
    )

    response = client.invoke_api_mapping_get(endpoint="test_process_endpoint", correlation_id="correl_id--1", _id="req_id--1", api_call_type=ApiCallType.SYNC)
    logger.info(
        f"API mapped endpoint invocation using GET returned %s", response
    )

    response = client.invoke_api_mapping_post(endpoint="test_process_endpoint", correlation_id="correl_id--1", _id="req_id--1", api_call_type=ApiCallType.SYNC, _input={"test": "value"})
    logger.info(
        f"API mapped endpoint invocation using POST returned %s", response
    )


    # current_directory_full_path = os.getcwd()
    #
    # if os.getenv("get_process_data"):
    #     process_data: ProcessData = client.get_process_data(8100103, True)
    #     print(str(process_data))
    #
    # if os.getenv("get_step_data"):
    #     step_data: StepData = client.get_step_data(8100123)
    #     print(str(step_data))
    #
    # if os.getenv("bulk_terminate"):
    #   bulk_terminate_response = client.bulk_terminate([8150036, 8150039], "Notesting from python SDK")
    #   print(str(bulk_terminate_response))
    #
    # if os.getenv("bulk_resume"):
    #   bulk_resume_response = client.bulk_resume([8150036, 8150039])
    #   print(str(bulk_resume_response))
    #
    # if os.getenv("bulk_review"):
    #     bulk_reviewed_response = client.bulk_reviewed([8150036, 8150039], "Reviewed sample")
    #     print(str(bulk_reviewed_response))
    #
    # if os.getenv("run_process"):
    #     process_request_data: ProcessRequestData = ProcessRequestData("Notesting", "default", 1, "abc", "abc",
    #                                                                   {"abc": "sample"})
    #     process_data: ProcessData = client.run_process_async(process_request_data)
    #     print(str(process_data.get_process_id()) + "," + str(process_data.get_status()))
    #
    # if os.getenv("rerun"):
    #     process_data : ProcessData = client.rerun(8150036)
    #     print(str(process_data))
    #
    # if os.getenv("search_process_executions"):
    #     process_search_request: ProcessSearchRequest = ProcessSearchRequest()
    #     process_search_request.set_process_ids([8200028, 8200025, 8200031])
    #     processes_data: list['ProcessData'] = client.search_process_executions(process_search_request)
    #     print(str(processes_data))
    #
    # if os.getenv("invoke_api_mapping_get"):
    #     response = client.invoke_api_mapping_get(endpoint="sample-endpoint/gYSrAHFzoTf7areCaznA/MRZ7lPU8keONrvR7Sc88", api_call_type=ApiCallType.ASYNC)
    #     print(str(response))
    #
    # if os.getenv("invoke_api_mapping_post"):
    #     response = client.invoke_api_mapping_post(endpoint="sample-endpoint/gYSrAHFzoTf7areCaznA/MRZ7lPU8keONrvR7Sc88", input={"Notesting": 123}, api_call_type=ApiCallType.ASYNC)
    #     print(str(response))
    #
    # if os.getenv("run_process"):
    #     process_data: ProcessData = client.run_process_sync(process_request_data)
    #     print(str(process_data.get_process_id()) + "," + str(process_data.get_status()))

    ## Both parameters are optional if both are supplied then scanning will be happening considering both if one of them is applied scanning will happen considering that else nothing will be registered
    ## we will ensure there are no duplicate workers registered (by name)
    ## decorator will be scanned by current_directory_full_path
    ## for callables references registration will be happened by decorator if provided else by function name itself
    # client.register_workers(current_directory_full_path)
    #
    # worker : Worker = Worker(manually_registered_worker, "manually_registered_worker")
    # client.register_worker(worker)
    #
    # worker : Worker = Worker(multiple_outputs, "multiple_outputs")
    # client.register_worker(worker)
    #
    #
    #
    # client.start()


if __name__ == "__main__":
    main()

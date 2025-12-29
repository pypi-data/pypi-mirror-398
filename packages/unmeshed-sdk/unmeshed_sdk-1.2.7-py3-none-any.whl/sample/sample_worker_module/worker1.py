import threading

from src.unmeshed.sdk.common.work_request import WorkRequest
from src.unmeshed.sdk.decorators.worker_function import worker_function
from unmeshed.sdk.unmeshed_client import UnmeshedClient


# noinspection PyUnusedLocal
@worker_function(name = "annotation_worker1", max_in_progress= 3)
def worker1(inp : str):
    work_request : WorkRequest = UnmeshedClient.get_current_work_request()
    print("Process Id : " + str(work_request.get_process_id()) + " and step Id : " + str(work_request.get_step_id()) + " for worker : worker1")
    return {
        "me": "Testing locally",
        "workRequest": work_request,
    }


# noinspection PyUnusedLocal
@worker_function(name = "python_secret_state_worker")
def secret_state_worker(inp: str):
    work_request : WorkRequest = UnmeshedClient.get_current_work_request()
    print("Process Id : " + str(work_request.get_process_id()) + " and step Id : " + str(work_request.get_step_id()) + "for worker : secret_state_worker")
    return {
        "__secretStatePut": {
            "abc": "sample",
            "booleanTest": True,
            "integerVar": 20,
            "nested": {
                "abc": "testing123"
            }
        }
    }
import os

from unmeshed.sdk.apis.workers.worker import Worker
from unmeshed.sdk.configs.client_config import ClientConfig
from unmeshed.sdk.decorators.worker_function import worker_function
from unmeshed.sdk.unmeshed_client import UnmeshedClient


@worker_function(name="worker3_test", namespace="default", max_in_progress=500)
def task_hello_world1(input_dict: dict) -> dict:
    # print(f"Received input: {input_dict}")
    output_dict = {
        "message": "Hello, world!",
        "input_received": input_dict
    }
    return output_dict

@worker_function(name="worker3_test", namespace="ns1", max_in_progress=500)
def task_hello_world2(input_dict: dict) -> dict:
    output_dict = {
        "message": "Hello, world!",
        "input_received": input_dict
    }
    return output_dict

def sample_worker(input_dict: dict) -> dict:
    output_dict = {
        "message": "Hello, world!",
        "input_received": input_dict
    }
    return output_dict

def main():
    client_config = ClientConfig()


    client_config.set_client_id("123")
    client_config.set_auth_token("123")
    client_config.set_port(8080)
    client_config.set_base_url("http://localhost")
    client_config.set_initial_delay_millis(50)
    client_config.set_step_timeout_millis(3600000)
    client_config.set_work_request_batch_size(200)
    client_config.set_response_submit_batch_size(1000)
    client_config.set_max_threads_count(10)
    client_config.set_poll_interval_millis(10)

    client = UnmeshedClient(client_config)
    current_directory_full_path = os.getcwd()
    client.register_decorated_workers(current_directory_full_path)
    client.register_worker(Worker(execution_method=sample_worker, namespace="ns1", name="test_worker"))
    client.register_worker(Worker(execution_method=sample_worker, namespace="default", name="test_worker"))

    client.start()


if __name__ == "__main__":
    main()

import time

from src.unmeshed.sdk.apis.workers.worker import Worker
from src.unmeshed.sdk.configs.client_config import ClientConfig
from unmeshed.sdk.unmeshed_client import UnmeshedClient, logger


def waiting_function(input_dict: dict) -> dict:
    time.sleep(0.1)
    logger.info("FINISHED sleeping for 30 seconds")
    output_dict = {
        "message": "Hello, world! waiting_function",
        "input_received": input_dict
    }
    return output_dict

def main():
    client_config = ClientConfig()
    client_config.set_client_id("26977084-83b0-43f8-98c9-21076d86393a")
    client_config.set_auth_token("s70frnUc3JB1orUqFI7r")
    client_config.set_port(8080)
    client_config.set_base_url("http://localhost")
    client_config.set_initial_delay_millis(50)
    client_config.set_step_timeout_millis(3600000)
    client_config.set_work_request_batch_size(200)
    client_config.set_response_submit_batch_size(1000)
    client_config.set_max_threads_count(100)
    client_config.set_poll_interval_millis(10)

    client = UnmeshedClient(client_config)

    wait_worker: Worker = Worker(waiting_function, "waiting_worker_2", "default", 1000)
    wait_worker.max_in_progress = 10000
    client.register_worker(wait_worker)
    client.start()


if __name__ == "__main__":
    main()

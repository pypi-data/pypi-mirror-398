import json

import requests

from ..http.http_client_factory import HttpClientFactory
from ..http.http_request_factory import HttpRequestFactory
from ...common.step_size import StepSize
from ...common.work_request import WorkRequest
from ...configs.client_config import ClientConfig
from ...logger_config import get_logger

logger = get_logger(__name__)

class PollerClient:
    CLIENTS_POLL_URL = "api/clients/poll"

    def __init__(self, client_config: ClientConfig, unmeshed_host_name : str, http_client_factory: HttpClientFactory,
                 http_request_factory: HttpRequestFactory):
        self.client_config = client_config
        self.unmeshed_host_name = unmeshed_host_name
        self.http_client = http_client_factory.create()
        self.http_request_factory = http_request_factory
        self.__polling_error_reported = False

    def poll(self, step_sizes: list['StepSize']) -> list['WorkRequest']:
        if not step_sizes:
            step_sizes = []

        json_body = []
        for step_size in step_sizes:
            json_body.append({
                "stepQueueNameData": {
                    "orgId": step_size.stepQueueNameData.orgId,
                    "namespace": step_size.stepQueueNameData.namespace,
                    "name": step_size.stepQueueNameData.name,
                    "stepType": step_size.stepQueueNameData.stepType.name,
                },
                "size": step_size.size
            })
        params = {
            "size": str(self.client_config.get_work_request_batch_size())
        }

        try:
            poll_request_headers = { "UNMESHED_HOST_NAME" : self.unmeshed_host_name}
            response = self.http_request_factory.create_post_request_with_headers(self.CLIENTS_POLL_URL, params=params, headers=poll_request_headers, body=json_body)
            response.raise_for_status()  # This will raise an HTTPError for bad responses

            if self.__polling_error_reported:
                self.__polling_error_reported = False
                logger.info("Polling for work resumed successfully")

        except requests.exceptions.HTTPError as http_err:
            self.__polling_error_reported = True
            logger.error("HTTP error occurred while polling: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            self.__polling_error_reported = True
            logger.error("Request error occurred while polling: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            self.__polling_error_reported = True
            logger.error("An unexpected error occurred while polling: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        if not response.text.strip():
            logger.debug("Did not receive any work, continuing to poll.")
            return []

        try:
            work_requests_dict_list = json.loads(response.text)

            return [
                WorkRequest(
                    processId=work_request_json.get("processId"),
                    stepId=work_request_json["stepId"],
                    stepExecutionId=work_request_json["stepExecutionId"],
                    stepName=work_request_json.get("stepName"),
                    stepRef=work_request_json.get("stepRef"),
                    stepNamespace=work_request_json.get("stepNamespace"),
                    inputParam=work_request_json["inputParam"],
                    isOptional=work_request_json.get("isOptional"),
                    polled=work_request_json["polled"],
                    scheduled=work_request_json["scheduled"],
                    updated=work_request_json["updated"],
                    priority=work_request_json["priority"],
                )
                for work_request_json in work_requests_dict_list
            ]
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err


import json
from dataclasses import asdict, fields
from enum import Enum
from typing import Any, TypeVar, Type, Optional

import requests

from ..http.http_client_factory import HttpClientFactory
from ..http.http_request_factory import HttpRequestFactory
from ...common.api_call_type import ApiCallType
from ...common.process_action_response_data import ProcessActionResponseData
from ...common.process_data import ProcessData
from ...common.process_definition import ProcessDefinition
from ...common.process_request_data import ProcessRequestData
from ...common.process_search_request import ProcessSearchRequest
from ...common.step_data import StepData
from ...configs.client_config import ClientConfig
from ...logger_config import get_logger

logger = get_logger(__name__)

class ProcessClient:
    def __init__(self, http_client_factory: HttpClientFactory,http_request_factory: HttpRequestFactory, client_config: ClientConfig):
        self.client_config = client_config
        self.__http_client = http_client_factory.create()
        self.http_request_factory = http_request_factory
        self.http_request_factory = http_request_factory
        self.__run_process_request_url = "api/process/"

    T = TypeVar('T')

    @staticmethod
    def dict_to_dataclass(data: dict, dataclass_type: Type[T]) -> T:
        valid_fields = {f.name for f in fields(dataclass_type)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return dataclass_type(**filtered_data)

    def __populate_single_process(self, process_data: dict) -> ProcessData:
        for key in ['orgId', 'eventType']:
            process_data.pop(key, None)
        return self.dict_to_dataclass(process_data, ProcessData)

    def __populate_process_data(self, process_data_json) -> ProcessData:
        return self.__populate_single_process(process_data_json)

    def __populate_processes_data(self, processes_data_json) -> list[ProcessData]:
        return [self.__populate_single_process(pd) for pd in processes_data_json]

    def __populate_step_data(self, step_data_json) -> StepData:
        return self.dict_to_dataclass(step_data_json, StepData)

    @staticmethod
    def __populate_process_action_response_data(bulk_termination_response) -> ProcessActionResponseData:
        return ProcessActionResponseData(
            count = bulk_termination_response.get("count"),
            details = bulk_termination_response.get("details")
        )

    def run_process_async(self, process_request_data: ProcessRequestData) -> ProcessData :
        params = {
            "clientId": self.client_config.get_client_id()
        }
        json_body = asdict(process_request_data) # type: ignore
        try:
            response = self.http_request_factory.create_post_request(self.__run_process_request_url + "runAsync",
                                                                     params=params,
                                                                     body=json_body)
            if response.status_code != 200:
                raise RuntimeError("Invalid process run request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while running process: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while running process: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while running process: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            process_data_json = json.loads(response.text)
            return self.__populate_process_data(process_data_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def run_process_sync(self, process_request_data: ProcessRequestData,
                         http_read_timeout: int,
                         process_timeout_seconds: int
                         ) -> ProcessData :
        params = {
            "clientId": self.client_config.get_client_id()
        }
        if process_timeout_seconds is not None:
            params["timeout"] = process_timeout_seconds
        try:
            json_body = asdict(process_request_data) # type: ignore
            response = self.http_request_factory.create_post_request(self.__run_process_request_url + "runSync",
                                                                     params=params,
                                                                     body=json_body,
                                                                     http_read_timeout=http_read_timeout)
            if response.status_code != 200:
                raise RuntimeError("Invalid process run request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while running process: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while running process: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while running process: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            process_data_json = json.loads(response.text)
            return self.__populate_process_data(process_data_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def get_process_data(self, process_id : int, include_steps: bool) -> ProcessData:
        if process_id  is None:
            raise ValueError("Process ID cannot be None")

        url = self.__run_process_request_url + "context/" + str(process_id)
        params = {
            "includeSteps": include_steps
        }
        try:
            response = self.http_request_factory.create_get_request(url, params=params)
            if response.status_code != 200:
                raise RuntimeError("Invalid fetch process data request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching process data: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred fetching process data: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred fetching process data: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            process_data_json = json.loads(response.text)
            return self.__populate_process_data(process_data_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def get_step_data(self, step_id : int) -> StepData:
        if step_id  is None:
            raise ValueError("Step ID cannot be None")
        url = self.__run_process_request_url + "stepContext/" + str(step_id)
        try:
            response = self.http_request_factory.create_get_request(url, params={})
            if response.status_code != 200:
                raise RuntimeError("Invalid fetch step data request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching step data: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while fetching step data: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while fetching step data: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            step_data_json = json.loads(response.text)
            return self.__populate_step_data(step_data_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def bulk_terminate(self, process_ids: list['int'], reason: str) -> ProcessActionResponseData:
        if process_ids is None:
            raise ValueError("ProcessIds's cannot be None")
        url = self.__run_process_request_url + "bulkTerminate"
        params = {}
        if reason is not None:
            params = {
                "reason": reason
            }
        try:
            response = self.http_request_factory.create_post_request(url, params, process_ids)
            if response.status_code != 200:
                raise RuntimeError("Failed to bulk terminate " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while bulk termination: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while bulk termination: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while bulk termination: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            bulk_termination_response = json.loads(response.text)
            return self.__populate_process_action_response_data(bulk_termination_response)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def bulk_resume(self, process_ids: list['int']) -> ProcessActionResponseData:
        if process_ids is None:
            raise ValueError("ProcessIds's cannot be None")
        url = self.__run_process_request_url + "bulkResume"
        params = {
            "clientId": self.client_config.get_client_id()
        }
        try:
            response = self.http_request_factory.create_post_request(url, params, process_ids)
            if response.status_code != 200:
                raise RuntimeError("Failed to bulk resume " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while bulk resume: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while bulk resume: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while bulk resume: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            bulk_resume_response = json.loads(response.text)
            return self.__populate_process_action_response_data(bulk_resume_response)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err


    def bulk_reviewed(self, process_ids: list['int'], reason: str) -> ProcessActionResponseData:
        if process_ids is None:
            raise ValueError("ProcessIds's cannot be None")
        url = self.__run_process_request_url + "bulkReviewed"
        params = {
            "clientId": self.client_config.get_client_id()
        }
        if reason is not None:
            params["reason"] = reason
        try:
            response = self.http_request_factory.create_post_request(url, params, process_ids)
            if response.status_code != 200:
                raise RuntimeError("Failed to bulk reviewed " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while bulk reviewed: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while bulk reviewed: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while bulk reviewed: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            bulk_reviewed_response = json.loads(response.text)
            return self.__populate_process_action_response_data(bulk_reviewed_response)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def rerun(self, process_id : int, version: int) -> ProcessData:
        if process_id is None:
            raise ValueError("Process ID cannot be None")
        params = {
            "clientId": self.client_config.get_client_id(),
            "processId": process_id
        }
        url = self.__run_process_request_url + "rerun"
        if version is not None:
            params["version"]= version

        try:
            response = self.http_request_factory.create_post_request(url, params, None)
            if response.status_code != 200:
                raise RuntimeError("Failed to rerun request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred rerunning process: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while rerunning process: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while rerunning process: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            process_data = json.loads(response.text)
            return self.__populate_process_data(process_data)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def search_process_executions(self, params: ProcessSearchRequest) -> list[ProcessData]:
        query_params = asdict(params)  # type: ignore
        # Convert list values to comma-separated strings
        query_params_filtered = {}
        for k, v in query_params.items():
            if v is not None:
                if isinstance(v, list):
                    query_params_filtered[k] = ",".join(str(x) for x in v)
                else:
                    query_params_filtered[k] = v

        url = "api/stats/process/search"

        try:
            response = self.http_request_factory.create_get_request(url, params=query_params_filtered)
            if response.status_code != 200:
                raise RuntimeError("Invalid fetch processes data " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching processes data: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred fetching processes data: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred fetching processes data: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            processes_data_json = json.loads(response.text)
            return self.__populate_processes_data(processes_data_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def invoke_api_mapping_get(self, endpoint: str, _id : str, correlation_id : str, api_call_type: ApiCallType) -> dict['str', 'Any']:
        query_params, url = self.validate_endpoint_and_get_url(api_call_type, correlation_id, endpoint, _id)
        try:
            response = self.http_request_factory.create_get_request(url, params=query_params)
            if response.status_code != 200:
                raise RuntimeError("Failed invoking webhook get request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while invoking webhook get request: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred invoking webhook get request: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred invoking webhook get request: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            response = json.loads(response.text)
            return response

        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    @staticmethod
    def validate_endpoint_and_get_url(api_call_type, correlation_id, endpoint, _id):
        if endpoint is None:
            raise ValueError("Endpoint cannot be None")
        query_params = {
            "id": _id if _id else None,
            "correlationId": correlation_id if correlation_id else None,
            "apiCallType": api_call_type.name if api_call_type else ApiCallType.ASYNC.name
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        url = "api/call/" + endpoint
        return query_params, url

    def invoke_api_mapping_post(self, endpoint: str, _input: dict['str', 'Any'], _id : str, correlation_id : str, api_call_type: ApiCallType) -> dict['str', 'Any']:
        query_params, url = self.validate_endpoint_and_get_url(api_call_type, correlation_id, endpoint, _id)
        try:
            response = self.http_request_factory.create_post_request(url, query_params, _input)
            if response.status_code != 200:
                raise RuntimeError("Failed invoking webhook post request " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while invoking webhook post request: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred invoking webhook post request: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred invoking webhook post request: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        try:
            response = json.loads(response.text)
            return response
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def get_process_definition_latest_or_version(self, namespace: str = "default", name: str = "",
                                                 version: Optional[int] = None) -> ProcessDefinition:
        query_params_filtered = {}
        url = "api/processDefinitions/" + namespace + "/" + name
        query_params_filtered["version"] = version

        try:
            response = self.http_request_factory.create_get_request(url, params=query_params_filtered)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error(
                    "Invalid response fetching latest or specific process definition version. Status: %s, Error: %s",
                    response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response fetching latest or specific process definition version (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching latest or specific process definition version: %s",
                         http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred fetching latest or specific process definition version: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred fetching latest or specific process definition version: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            process_definition_json = json.loads(response.text)
            # Filter out unwanted fields
            filtered_json = {k: v for k, v in process_definition_json.items() if
                             k not in ['signature', 'dependencies', 'dependents']}
            process_definition: ProcessDefinition = self.dict_to_dataclass(filtered_json, ProcessDefinition)
            return process_definition
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def get_all_process_definitions(self) -> list[ProcessDefinition]:
        query_params_filtered = {}
        url = "api/processDefinitions"

        try:
            response = self.http_request_factory.create_get_request(url, params=query_params_filtered)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error("Invalid response fetching process definitions. Status: %s, Error: %s",
                             response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response fetching process definitions (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching process definition: %s", http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred fetching process definition: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred fetching process definition: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            process_definitions_json = json.loads(response.text)
            # Filter out unwanted fields before converting
            process_definitions: list[ProcessDefinition] = [
                self.dict_to_dataclass(
                    {k: v for k, v in item.items() if k not in ['signature', 'dependencies', 'dependents']},
                    ProcessDefinition)
                for item in process_definitions_json
            ]
            return process_definitions
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def _serialize_value(self, obj):
        """Helper function to serialize objects including Enums"""
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._serialize_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_value(item) for item in obj]
        return obj

    def create_new_process_definition(self, process_definition: ProcessDefinition) -> ProcessDefinition:
        query_params_filtered = {}
        url = "api/processDefinitions"

        try:
            # Convert ProcessDefinition object to dictionary and handle Enums
            body_dict = asdict(process_definition)
            body = self._serialize_value(body_dict)

            response = self.http_request_factory.create_post_request(url, params=query_params_filtered,
                                                                     body=body)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error("Invalid response creating process definition. Status: %s, Error: %s",
                             response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response creating process definition (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while creating process definition: %s", http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred creating process definition: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred creating process definition: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            process_definition_json = json.loads(response.text)
            # Filter out unwanted fields
            filtered_json = {k: v for k, v in process_definition_json.items() if
                             k not in ['signature', 'dependencies', 'dependents']}
            process_definition: ProcessDefinition = self.dict_to_dataclass(filtered_json, ProcessDefinition)
            return process_definition
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def update_process_definition(self, process_definition: ProcessDefinition) -> ProcessDefinition:
        query_params_filtered = {}
        url = "api/processDefinitions"

        try:
            # Convert ProcessDefinition object to dictionary and handle Enums
            body_dict = asdict(process_definition)
            body = self._serialize_value(body_dict)

            response = self.http_request_factory.create_put_request(url, params=query_params_filtered,
                                                                    body=body)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error("Invalid response updating process definition. Status: %s, Error: %s",
                             response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response updating process definition (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while updating process definition: %s", http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred updating process definition: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred updating process definition: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            process_definition_json = json.loads(response.text)
            # Filter out unwanted fields
            filtered_json = {k: v for k, v in process_definition_json.items() if
                             k not in ['signature', 'dependencies', 'dependents']}
            process_definition: ProcessDefinition = self.dict_to_dataclass(filtered_json, ProcessDefinition)
            return process_definition
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def delete_process_definitions(self, process_definitions: list[ProcessDefinition], version_only: bool) -> Any:

        query_params_filtered = {}
        url = "api/processDefinitions"
        query_params_filtered["versionOnly"] = version_only

        try:
            # Convert ProcessDefinition objects to dictionaries and handle Enums
            body = [self._serialize_value(asdict(pd)) for pd in process_definitions]

            response = self.http_request_factory.create_delete_request(url, params=query_params_filtered,
                                                                       body=body)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error("Invalid response deleting process definitions. Status: %s, Error: %s",
                             response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response deleting process definitions (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while deleting process definitions: %s", http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred deleting process definitions: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred deleting process definitions: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            delete_response = json.loads(response.text)
            return delete_response
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def get_process_definition_versions(self, namespace: str = "default", name: str = "") -> list[int]:
        url = f"api/processDefinitions/{namespace}/{name}/versions"

        try:
            response = self.http_request_factory.create_get_request(url)
            if response.status_code != 200:
                error_details = response.text
                try:
                    error_json = json.loads(error_details)
                    error_message = error_json.get('errorMessage', error_details)
                except:
                    error_message = error_details

                logger.error("Invalid response fetching process definition versions. Status: %s, Error: %s",
                             response.status_code, error_message)
                raise RuntimeError(
                    f"Invalid response fetching process definition versions (Status {response.status_code}): {error_message}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching process definition versions: %s", http_err)
            try:
                error_json = json.loads(http_err.response.text)
                error_message = error_json.get('errorMessage', str(http_err))
            except:
                error_message = str(http_err)
            raise RuntimeError(f"HTTP error: {error_message}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred fetching process definition versions: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred fetching process definition versions: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            data = response.json()
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err
        if isinstance(data, list):
            try:
                versions = [int(v) for v in data]
                return versions
            except (ValueError, TypeError):
                logger.warning("Received non-integer version list: %s", data)
                return data
        else:
            raise RuntimeError(f"Expected list response but got: {type(data).__name__}")
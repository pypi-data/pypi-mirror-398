from dataclasses import dataclass, field
from typing import List

from ..common.poll_request_data import PollRequestData


@dataclass
class ClientConfig:
    namespace: str = "default"
    base_url: str = "http://localhost"
    port: int = 8080
    connection_timeout_secs: int = 60
    submit_client_poll_timeout_seconds: float = 30
    poll_interval_millis: int = 100
    step_timeout_millis: int = 5000
    initial_delay_millis: int = 1000
    work_request_batch_size: int = 100
    step_submission_attempts: int = 3
    client_id: str = ""
    auth_token: str = ""
    max_threads_count: int = 20
    poll_request_data: PollRequestData = None
    response_submit_batch_size: int = 500
    __permanent_error_keywords: List[str] = field(default_factory=lambda: [
        "Invalid request, step is not in RUNNING state",
        "please poll the latest and update"
    ])
    max_submit_attempts: int = 50
    enable_results_submission = True

    @property
    def permanent_error_keywords(self) -> List[str]:
        """Read-only property for permanent_error_keywords."""
        return self.__permanent_error_keywords

    def has_token(self) -> bool:
        """Check if the auth_token is valid (non-empty and non-whitespace)."""
        return bool(self.auth_token and self.auth_token.strip())

    def get_client_id(self) -> str:
        """Getter method for client_id."""
        return self.client_id

    def get_base_url(self) -> str:
        """Getter method for base_url."""
        return self.base_url

    def get_port(self) -> int:
        """Getter method for port."""
        return self.port

    def get_initial_delay_millis(self) -> int:
        """Getter method for initial_delay_millis."""
        return self.initial_delay_millis

    def get_step_timeout_millis(self) -> int:
        """Getter method for step_timeout_millis."""
        return self.step_timeout_millis

    def get_step_submission_attempts(self) -> int:
        """Getter method for step_submission_attempts."""
        return self.step_submission_attempts

    def get_max_threads_count(self) -> int:
        """Getter method for max_threads_count."""
        return self.max_threads_count

    def get_poll_request_data(self) -> PollRequestData:
        """Getter method for poll_request_data."""
        return self.poll_request_data

    # Setter methods for each field
    def set_namespace(self, namespace: str):
        """Setter for namespace."""
        self.namespace = namespace

    def set_base_url(self, base_url: str):
        """Setter for base_url."""
        self.base_url = base_url

    def set_port(self, port: int):
        """Setter for port."""
        self.port = port

    def set_connection_timeout_secs(self, connection_timeout_secs: int):
        """Setter for connection_timeout_secs."""
        self.connection_timeout_secs = connection_timeout_secs

    def set_step_timeout_millis(self, step_timeout_millis: int):
        """Setter for step_timeout_millis."""
        self.step_timeout_millis = step_timeout_millis

    def set_initial_delay_millis(self, initial_delay_millis: int):
        """Setter for initial_delay_millis."""
        self.initial_delay_millis = initial_delay_millis

    def set_work_request_batch_size(self, work_request_batch_size: int):
        """Setter for work_request_batch_size."""
        self.work_request_batch_size = work_request_batch_size

    def get_work_request_batch_size(self) -> int:
        return self.work_request_batch_size

    def set_step_submission_attempts(self, step_submission_attempts: int):
        """Setter for step_submission_attempts."""
        self.step_submission_attempts = step_submission_attempts

    def set_client_id(self, client_id: str):
        """Setter for client_id."""
        self.client_id = client_id

    def set_auth_token(self, auth_token: str):
        """Setter for auth_token."""
        self.auth_token = auth_token

    def get_auth_token(self) -> str:
        return self.auth_token

    def set_max_threads_count(self, max_threads_count: int):
        """Setter for max_threads_count."""
        self.max_threads_count = max_threads_count

    def set_poll_request_data(self, poll_request_data: PollRequestData):
        """Setter for poll_request_data."""
        self.poll_request_data = poll_request_data

    def set_response_submit_batch_size(self, response_submit_batch_size: int):
        self.response_submit_batch_size = response_submit_batch_size

    def get_response_submit_batch_size(self) -> int:
        return self.response_submit_batch_size

    def set_max_submit_attempts(self, max_submit_attempts: int):
        self.max_submit_attempts = max_submit_attempts

    def get_max_submit_attempts(self) -> int:
        return self.max_submit_attempts

    def set_poll_interval_millis(self, poll_interval_millis: int):
        self.poll_interval_millis = poll_interval_millis

    def get_poll_interval_millis(self) -> int:
        return self.poll_interval_millis

    def set_submit_client_poll_timeout_seconds(self, submit_client_poll_timeout_seconds: float):
        self.submit_client_poll_timeout_seconds = submit_client_poll_timeout_seconds

    def get_submit_client_poll_timeout_seconds(self)-> float:
        return self.submit_client_poll_timeout_seconds

    def set_enable_results_submission(self, enable_results_submission: bool):
        self.enable_results_submission = enable_results_submission

    def is_enable_results_submission(self) -> bool:
        return self.enable_results_submission

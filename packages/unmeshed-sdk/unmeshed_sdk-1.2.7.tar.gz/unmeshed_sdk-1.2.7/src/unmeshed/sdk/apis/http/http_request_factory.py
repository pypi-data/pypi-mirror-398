from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

from ...configs.client_config import ClientConfig
from ...logger_config import get_logger
from ...utils.unmeshed_common_utils import UnmeshedCommonUtils

logger = get_logger(__name__)

class HttpRequestFactory:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config
        self.base_url = client_config.get_base_url()
        self.port = client_config.get_port()
        self.bearer_value = f"Bearer client.sdk.{self.client_config.get_client_id()}.{UnmeshedCommonUtils.create_secure_hash(self.client_config.get_auth_token())}"

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": self.bearer_value,
            "Connection": "keep-alive"
        })
        # noinspection HttpUrlsUsage
        self.session.mount('http://', HTTPAdapter(pool_connections=2, pool_maxsize=10, max_retries=3))
        self.session.mount('https://', HTTPAdapter(pool_connections=2, pool_maxsize=10, max_retries=3))

    def __build_uri(self, path: str) -> str:
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        parsed_url = urlparse(self.base_url)
        has_port = parsed_url.port is not None
        url = f"{self.base_url}/{path}" if has_port or self.base_url.startswith(
            "https:") else f"{self.base_url}:{self.port}/{path}"

        return url

    def _make_request(self, method, path, params=None, body=None, headers=None, timeout=10):
        uri = self.__build_uri(path)

        try:
            response = self.session.request(method, uri, json=body, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error("Request failed : %s", e)
            raise

    def create_get_request(self, path, params=None):
        return self._make_request("GET", path, params)

    def create_post_request(self, path, params=None, body=None, http_read_timeout=10):
        return self._make_request("POST", path, params, body, timeout=http_read_timeout)

    def create_post_request_with_headers(self, path, params=None, headers=None, body=None, http_read_timeout=10):
        return self._make_request("POST", path, params, body, headers, timeout=http_read_timeout)

    def create_put_request(self, path, params=None, body=None):
        return self._make_request("PUT", path, params, body)

    def create_post_request_with_body(self, path, body=None):
        return self.create_post_request(path, body=body)

    def create_delete_request(self, path, params=None, body=None, http_read_timeout=10):
        return self._make_request("DELETE", path, params, body, timeout=http_read_timeout)



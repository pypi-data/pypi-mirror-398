import http.client
import http.client as http_client

from ...configs.client_config import ClientConfig

class HttpClientFactory:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    def create(self) -> http_client.HTTPConnection:
        timeout = self.client_config.connection_timeout_secs
        conn = http.client.HTTPConnection("httpbin.org", timeout=timeout)
        return conn
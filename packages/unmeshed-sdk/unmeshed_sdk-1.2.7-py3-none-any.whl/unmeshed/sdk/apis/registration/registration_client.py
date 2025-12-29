import time

from ..http.http_client_factory import HttpClientFactory
from ..http.http_request_factory import HttpRequestFactory
from ..workers.worker import Worker
from ...configs.client_config import ClientConfig
from ...logger_config import get_logger

logger = get_logger(__name__)

class RegistrationClient:
    CLIENTS_REGISTER_URL = "api/clients/register"

    def __init__(self, client_config: ClientConfig, http_client_factory: HttpClientFactory,
                 http_request_factory: HttpRequestFactory):
        self.client_config = client_config
        self.http_client = http_client_factory.create()
        self.request_factory = http_request_factory
        self.__workers: list[Worker] = []

    def add_workers(self, workers: list[Worker]):
        self.__workers.extend(workers)

    def renew_registration(self) -> str:
        supported_steps = [
            {
                "orgId": 0,
                "namespace": worker.namespace,
                "stepType": "WORKER",
                "name": worker.name
            }
            for worker in self.__workers
        ]

        logger.info("Renewing registration for the following workers: %s", supported_steps)

        params = {}
        delay = 2

        while True:
            try:
                response = self.request_factory.create_put_request(
                    self.CLIENTS_REGISTER_URL, params=params, body=supported_steps
                )
                logger.debug("Response from server: %s", response)

                if response.status_code == 200:
                    logger.info("Successfully renewed registration for workers.")
                    return response.text
                else:
                    logger.error("Did not receive 200! %s", response.text)
                    raise Exception(
                        f"Got a non-200 result from the server when trying to renew registration: {response.status_code}"
                    )
            except Exception as e:
                logger.error("An error occurred while renewing registration: %s", str(e))

            logger.info("Retrying in %d seconds...", delay)
            time.sleep(delay)

    def get_workers(self) -> list[Worker]:
        return self.__workers
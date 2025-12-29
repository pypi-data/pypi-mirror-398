from abc import ABC, abstractmethod
from Crypto.PublicKey.RSA import RsaKey
from typing import Generic
from nexo.database.handlers import RedisHandler
from nexo.logging.config import LogConfig
from nexo.logging.logger import Client
from nexo.schemas.application import ApplicationContext, OptApplicationContext
from nexo.schemas.google import ListOfPublisherHandlers
from .http import HTTPClientManager
from .config import ClientConfigT


class ClientManager(ABC, Generic[ClientConfigT]):
    def __init__(
        self,
        *,
        application_context: OptApplicationContext = None,
        config: ClientConfigT,
        log_config: LogConfig,
        private_key: RsaKey,
        redis: RedisHandler,
        publishers: ListOfPublisherHandlers = [],
    ):
        self._application_context = (
            application_context
            if application_context is not None
            else ApplicationContext.new()
        )
        self._config = config
        self._log_config = log_config

        self._key = self._config.key
        self._name = self._config.name

        self._logger = Client(
            environment=self._application_context.environment,
            service_key=self._application_context.service_key,
            client_key=self._key,
            config=log_config,
        )

        self._http_client_manager = HTTPClientManager()
        self._private_key = private_key
        self._redis = redis
        self._publishers = publishers

        self.initalize_services()
        self._logger.info(f"{self._name} client manager initialized successfully")

    @abstractmethod
    def initalize_services(self):
        """Initialize all services of this client"""

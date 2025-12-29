from Crypto.PublicKey.RSA import RsaKey
from typing import ClassVar, Generic
from nexo.database.enums import CacheOrigin, CacheLayer
from nexo.database.handlers import RedisHandler
from nexo.logging.logger import Client
from nexo.schemas.application import ApplicationContext, OptApplicationContext
from nexo.schemas.google import ListOfPublisherHandlers
from nexo.schemas.operation.context import generate
from nexo.schemas.operation.enums import Origin, Layer, Target
from nexo.schemas.resource import Resource, AggregateField
from .http import HTTPClientManager
from .config import ClientConfigT


class ClientService(Generic[ClientConfigT]):
    _resource: ClassVar[Resource]

    def __init__(
        self,
        *,
        application_context: OptApplicationContext = None,
        config: ClientConfigT,
        logger: Client,
        http_client_manager: HTTPClientManager,
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
        self._logger = logger
        self._http_client_manager = http_client_manager
        self._private_key = private_key
        self._redis = redis
        self._publishers = publishers

        self._namespace = self._redis.config.build_namespace(
            self._resource.aggregate(AggregateField.KEY, sep=":"),
            client=self._config.key,
            origin=CacheOrigin.CLIENT,
            layer=CacheLayer.SERVICE,
        )

        self._operation_context = generate(
            origin=Origin.CLIENT, layer=Layer.SERVICE, target=Target.INTERNAL
        )

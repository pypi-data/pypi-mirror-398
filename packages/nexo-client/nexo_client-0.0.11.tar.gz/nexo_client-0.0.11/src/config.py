from pydantic import BaseModel, Field
from typing import Annotated, Generic, TypeVar
from nexo.enums.environment import EnvironmentMixin, Environment


class ClientConfig(EnvironmentMixin[Environment]):
    key: Annotated[str, Field(..., description="Client's key")]
    name: Annotated[str, Field(..., description="Client's name")]
    url: str = Field(..., description="Client's URL")


ClientConfigT = TypeVar("ClientConfigT", bound=ClientConfig)


class ClientConfigs(BaseModel):
    pass


OptClientConfigs = ClientConfigs | None
OptClientConfigsT = TypeVar("OptClientConfigsT", bound=OptClientConfigs)


class ClientConfigsMixin(BaseModel, Generic[OptClientConfigsT]):
    clients: OptClientConfigsT = Field(..., description="Client config")

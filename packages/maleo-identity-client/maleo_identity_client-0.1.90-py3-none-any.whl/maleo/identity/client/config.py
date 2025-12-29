from pydantic import Field
from typing import Annotated
from nexo.client.config import ClientConfig as BaseClientConfig
from maleo.enums.service import ServiceKey, ServiceName


class ClientConfig(BaseClientConfig):
    key: Annotated[
        str, Field(ServiceKey.IDENTITY.value, description="Client's key")
    ] = ServiceKey.IDENTITY.value
    name: Annotated[
        str, Field(ServiceName.IDENTITY.value, description="Client's name")
    ] = ServiceName.IDENTITY.value

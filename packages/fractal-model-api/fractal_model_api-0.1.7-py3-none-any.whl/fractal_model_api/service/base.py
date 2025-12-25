from dataclasses import dataclass
from typing import TypedDict, ClassVar, Generic, TypeVar


class ServiceConfig(TypedDict):
    resource: str


class RequestConfig(TypedDict):
    action: str


_TResponse = TypeVar("_TResponse")


@dataclass
class BaseRequest(Generic[_TResponse]):
    service_config: ClassVar[ServiceConfig]
    request_config: ClassVar[RequestConfig]

    def serialize(self):
        return self.__dict__

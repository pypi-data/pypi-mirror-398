from ..base import BaseRequest, _TResponse, ServiceConfig


class OptimizerRequest(BaseRequest[_TResponse]):
    service_config = ServiceConfig(
        resource="optimizer"
    )
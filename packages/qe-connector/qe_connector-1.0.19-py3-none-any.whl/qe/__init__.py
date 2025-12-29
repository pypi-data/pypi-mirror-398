"""
QE Connector Python SDK
"""
from .api import API
from .error import (
    Error,
    ClientError,
    APIError,
    ServerError,
    ParameterRequiredError,
    ParameterValueError,
    ParameterTypeError,
    ParameterArgumentError,
    WebsocketClientError
)

# WebSocket相关导入
from .ws import (
    WebSocketService,
    WebSocketEventHandlers,
    ClientPushMessage,
    MasterOrderMessage,
    OrderMessage,
    FillMessage,
    BaseThirdPartyMessage,
    ClientMessageType,
    ThirdPartyMessageType
)

__version__ = "1.0.4"

__all__ = [
    'API',
    'Error',
    'ClientError',
    'APIError',
    'ServerError',
    'ParameterRequiredError',
    'ParameterValueError',
    'ParameterTypeError',
    'ParameterArgumentError',
    'WebsocketClientError',
    'WebSocketService',
    'WebSocketEventHandlers',
    'ClientPushMessage',
    'MasterOrderMessage',
    'OrderMessage',
    'FillMessage',
    'BaseThirdPartyMessage',
    'ClientMessageType',
    'ThirdPartyMessageType'
]

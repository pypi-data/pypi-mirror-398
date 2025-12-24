from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.subscriptions import world_subscription_request_pb2 as _world_subscription_request_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SubscribeWorldSubscriptionRequestsResponse(_message.Message):
    __slots__ = ("request",)
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    request: _world_subscription_request_pb2.WorldSubscriptionRequest
    def __init__(self, request: _Optional[_Union[_world_subscription_request_pb2.WorldSubscriptionRequest, _Mapping]] = ...) -> None: ...

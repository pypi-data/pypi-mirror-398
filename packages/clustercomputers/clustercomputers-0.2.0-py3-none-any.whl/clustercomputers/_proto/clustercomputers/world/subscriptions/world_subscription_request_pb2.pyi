from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.subscriptions import world_subscription_pb2 as _world_subscription_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldSubscriptionRequest(_message.Message):
    __slots__ = ("subscribe", "subscription")
    SUBSCRIBE_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    subscribe: bool
    subscription: _world_subscription_pb2.WorldSubscription
    def __init__(self, subscribe: bool = ..., subscription: _Optional[_Union[_world_subscription_pb2.WorldSubscription, str]] = ...) -> None: ...

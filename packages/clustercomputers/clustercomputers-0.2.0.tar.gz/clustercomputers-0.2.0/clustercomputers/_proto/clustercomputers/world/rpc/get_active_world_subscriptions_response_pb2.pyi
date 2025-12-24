from clustercomputers._proto.clustercomputers.world.subscriptions import world_subscription_pb2 as _world_subscription_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetActiveWorldSubscriptionsResponse(_message.Message):
    __slots__ = ("subscriptions",)
    SUBSCRIPTIONS_FIELD_NUMBER: _ClassVar[int]
    subscriptions: _containers.RepeatedScalarFieldContainer[_world_subscription_pb2.WorldSubscription]
    def __init__(self, subscriptions: _Optional[_Iterable[_Union[_world_subscription_pb2.WorldSubscription, str]]] = ...) -> None: ...

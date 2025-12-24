from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.subscriptions import redstone_update_pb2 as _redstone_update_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldSubscriptionUpdate(_message.Message):
    __slots__ = ("redstone_update",)
    REDSTONE_UPDATE_FIELD_NUMBER: _ClassVar[int]
    redstone_update: _redstone_update_pb2.RedstoneUpdate
    def __init__(self, redstone_update: _Optional[_Union[_redstone_update_pb2.RedstoneUpdate, _Mapping]] = ...) -> None: ...

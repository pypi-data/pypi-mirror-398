from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import pending_world_action_pb2 as _pending_world_action_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetPendingWorldActionsResponse(_message.Message):
    __slots__ = ("action",)
    ACTION_FIELD_NUMBER: _ClassVar[int]
    action: _pending_world_action_pb2.PendingWorldAction
    def __init__(self, action: _Optional[_Union[_pending_world_action_pb2.PendingWorldAction, _Mapping]] = ...) -> None: ...

from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_pb2 as _world_action_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_status_pb2 as _world_action_status_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetWorldActionResponse(_message.Message):
    __slots__ = ("action", "status")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    action: _world_action_pb2.WorldAction
    status: _world_action_status_pb2.WorldActionStatus
    def __init__(self, action: _Optional[_Union[_world_action_pb2.WorldAction, _Mapping]] = ..., status: _Optional[_Union[_world_action_status_pb2.WorldActionStatus, _Mapping]] = ...) -> None: ...

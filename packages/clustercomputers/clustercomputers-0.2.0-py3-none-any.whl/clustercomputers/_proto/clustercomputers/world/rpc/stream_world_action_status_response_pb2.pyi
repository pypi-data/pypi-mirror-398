from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_status_pb2 as _world_action_status_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_result_pb2 as _world_result_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamWorldActionStatusResponse(_message.Message):
    __slots__ = ("initial_status", "payload_processed")
    INITIAL_STATUS_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_PROCESSED_FIELD_NUMBER: _ClassVar[int]
    initial_status: _world_action_status_pb2.WorldActionStatus
    payload_processed: _world_result_pb2.WorldResult
    def __init__(self, initial_status: _Optional[_Union[_world_action_status_pb2.WorldActionStatus, _Mapping]] = ..., payload_processed: _Optional[_Union[_world_result_pb2.WorldResult, _Mapping]] = ...) -> None: ...

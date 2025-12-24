from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_id_pb2 as _world_action_id_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_result_pb2 as _world_result_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IndexedWorldResult(_message.Message):
    __slots__ = ("id", "index", "result")
    ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    id: _world_action_id_pb2.WorldActionId
    index: int
    result: _world_result_pb2.WorldResult
    def __init__(self, id: _Optional[_Union[_world_action_id_pb2.WorldActionId, _Mapping]] = ..., index: _Optional[int] = ..., result: _Optional[_Union[_world_result_pb2.WorldResult, _Mapping]] = ...) -> None: ...

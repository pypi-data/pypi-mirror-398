from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import indexed_world_result_pb2 as _indexed_world_result_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SendWorldResultRequest(_message.Message):
    __slots__ = ("result",)
    RESULT_FIELD_NUMBER: _ClassVar[int]
    result: _indexed_world_result_pb2.IndexedWorldResult
    def __init__(self, result: _Optional[_Union[_indexed_world_result_pb2.IndexedWorldResult, _Mapping]] = ...) -> None: ...

from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import redstone_sides_pb2 as _redstone_sides_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SetAllRedstoneOutputs(_message.Message):
    __slots__ = ("sides",)
    SIDES_FIELD_NUMBER: _ClassVar[int]
    sides: _redstone_sides_pb2.RedstoneSides
    def __init__(self, sides: _Optional[_Union[_redstone_sides_pb2.RedstoneSides, _Mapping]] = ...) -> None: ...

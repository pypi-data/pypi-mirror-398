from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import block_location_pb2 as _block_location_pb2
from clustercomputers._proto.clustercomputers.world.model import redstone_sides_pb2 as _redstone_sides_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldResult(_message.Message):
    __slots__ = ("value", "failure_message")
    class Value(_message.Message):
        __slots__ = ("block_location", "redstone_sides")
        BLOCK_LOCATION_FIELD_NUMBER: _ClassVar[int]
        REDSTONE_SIDES_FIELD_NUMBER: _ClassVar[int]
        block_location: _block_location_pb2.BlockLocation
        redstone_sides: _redstone_sides_pb2.RedstoneSides
        def __init__(self, block_location: _Optional[_Union[_block_location_pb2.BlockLocation, _Mapping]] = ..., redstone_sides: _Optional[_Union[_redstone_sides_pb2.RedstoneSides, _Mapping]] = ...) -> None: ...
    VALUE_FIELD_NUMBER: _ClassVar[int]
    FAILURE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    value: WorldResult.Value
    failure_message: str
    def __init__(self, value: _Optional[_Union[WorldResult.Value, _Mapping]] = ..., failure_message: _Optional[str] = ...) -> None: ...

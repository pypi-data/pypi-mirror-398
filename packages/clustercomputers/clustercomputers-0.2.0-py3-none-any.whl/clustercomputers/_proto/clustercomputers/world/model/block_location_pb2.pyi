from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import block_position_pb2 as _block_position_pb2
from clustercomputers._proto.clustercomputers.world.model import cardinal_direction_pb2 as _cardinal_direction_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BlockLocation(_message.Message):
    __slots__ = ("dimension", "position", "facing")
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    FACING_FIELD_NUMBER: _ClassVar[int]
    dimension: str
    position: _block_position_pb2.BlockPosition
    facing: _cardinal_direction_pb2.CardinalDirection
    def __init__(self, dimension: _Optional[str] = ..., position: _Optional[_Union[_block_position_pb2.BlockPosition, _Mapping]] = ..., facing: _Optional[_Union[_cardinal_direction_pb2.CardinalDirection, str]] = ...) -> None: ...

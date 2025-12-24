from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import block_side_pb2 as _block_side_pb2
from clustercomputers._proto.clustercomputers.world.model import redstone_signal_pb2 as _redstone_signal_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SideRedstoneSignal(_message.Message):
    __slots__ = ("side", "signal")
    SIDE_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    side: _block_side_pb2.BlockSide
    signal: _redstone_signal_pb2.RedstoneSignal
    def __init__(self, side: _Optional[_Union[_block_side_pb2.BlockSide, str]] = ..., signal: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ...) -> None: ...

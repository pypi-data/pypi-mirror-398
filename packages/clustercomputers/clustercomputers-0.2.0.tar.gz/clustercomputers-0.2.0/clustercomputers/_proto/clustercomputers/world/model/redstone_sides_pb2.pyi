from clustercomputers._proto.clustercomputers.world.model import redstone_signal_pb2 as _redstone_signal_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RedstoneSides(_message.Message):
    __slots__ = ("front", "back", "left", "right", "top", "bottom")
    FRONT_FIELD_NUMBER: _ClassVar[int]
    BACK_FIELD_NUMBER: _ClassVar[int]
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    TOP_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_FIELD_NUMBER: _ClassVar[int]
    front: _redstone_signal_pb2.RedstoneSignal
    back: _redstone_signal_pb2.RedstoneSignal
    left: _redstone_signal_pb2.RedstoneSignal
    right: _redstone_signal_pb2.RedstoneSignal
    top: _redstone_signal_pb2.RedstoneSignal
    bottom: _redstone_signal_pb2.RedstoneSignal
    def __init__(self, front: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ..., back: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ..., left: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ..., right: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ..., top: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ..., bottom: _Optional[_Union[_redstone_signal_pb2.RedstoneSignal, _Mapping]] = ...) -> None: ...

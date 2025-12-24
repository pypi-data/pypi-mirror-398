from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.model import side_redstone_signal_pb2 as _side_redstone_signal_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RedstoneUpdate(_message.Message):
    __slots__ = ("input",)
    INPUT_FIELD_NUMBER: _ClassVar[int]
    input: _side_redstone_signal_pb2.SideRedstoneSignal
    def __init__(self, input: _Optional[_Union[_side_redstone_signal_pb2.SideRedstoneSignal, _Mapping]] = ...) -> None: ...

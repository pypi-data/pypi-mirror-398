from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Sleep(_message.Message):
    __slots__ = ("ticks",)
    TICKS_FIELD_NUMBER: _ClassVar[int]
    ticks: int
    def __init__(self, ticks: _Optional[int] = ...) -> None: ...

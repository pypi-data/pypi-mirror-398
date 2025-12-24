from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_payload_pb2 as _world_payload_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateWorldActionRequest(_message.Message):
    __slots__ = ("payloads",)
    PAYLOADS_FIELD_NUMBER: _ClassVar[int]
    payloads: _containers.RepeatedCompositeFieldContainer[_world_payload_pb2.WorldPayload]
    def __init__(self, payloads: _Optional[_Iterable[_Union[_world_payload_pb2.WorldPayload, _Mapping]]] = ...) -> None: ...

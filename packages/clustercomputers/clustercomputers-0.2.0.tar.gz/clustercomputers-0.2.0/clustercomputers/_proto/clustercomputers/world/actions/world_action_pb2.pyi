from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_id_pb2 as _world_action_id_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_payload_pb2 as _world_payload_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldAction(_message.Message):
    __slots__ = ("id", "track_status", "payloads")
    ID_FIELD_NUMBER: _ClassVar[int]
    TRACK_STATUS_FIELD_NUMBER: _ClassVar[int]
    PAYLOADS_FIELD_NUMBER: _ClassVar[int]
    id: _world_action_id_pb2.WorldActionId
    track_status: bool
    payloads: _containers.RepeatedCompositeFieldContainer[_world_payload_pb2.WorldPayload]
    def __init__(self, id: _Optional[_Union[_world_action_id_pb2.WorldActionId, _Mapping]] = ..., track_status: bool = ..., payloads: _Optional[_Iterable[_Union[_world_payload_pb2.WorldPayload, _Mapping]]] = ...) -> None: ...

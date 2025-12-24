from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_action_id_pb2 as _world_action_id_pb2
from clustercomputers._proto.clustercomputers.world.actions import world_result_pb2 as _world_result_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldActionStatus(_message.Message):
    __slots__ = ("id", "state", "results")
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATE_UNSPECIFIED: _ClassVar[WorldActionStatus.State]
        STATE_PENDING: _ClassVar[WorldActionStatus.State]
        STATE_SUCCEEDED: _ClassVar[WorldActionStatus.State]
        STATE_FAILED: _ClassVar[WorldActionStatus.State]
    STATE_UNSPECIFIED: WorldActionStatus.State
    STATE_PENDING: WorldActionStatus.State
    STATE_SUCCEEDED: WorldActionStatus.State
    STATE_FAILED: WorldActionStatus.State
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    id: _world_action_id_pb2.WorldActionId
    state: WorldActionStatus.State
    results: _containers.RepeatedCompositeFieldContainer[_world_result_pb2.WorldResult]
    def __init__(self, id: _Optional[_Union[_world_action_id_pb2.WorldActionId, _Mapping]] = ..., state: _Optional[_Union[WorldActionStatus.State, str]] = ..., results: _Optional[_Iterable[_Union[_world_result_pb2.WorldResult, _Mapping]]] = ...) -> None: ...

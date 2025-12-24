from clustercomputers._proto.buf.validate import validate_pb2 as _validate_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_location_pb2 as _get_location_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_redstone_inputs_pb2 as _get_redstone_inputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import get_redstone_outputs_pb2 as _get_redstone_outputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import ring_bell_pb2 as _ring_bell_pb2
from clustercomputers._proto.clustercomputers.world.actions import set_all_redstone_outputs_pb2 as _set_all_redstone_outputs_pb2
from clustercomputers._proto.clustercomputers.world.actions import set_redstone_output_pb2 as _set_redstone_output_pb2
from clustercomputers._proto.clustercomputers.world.actions import sleep_pb2 as _sleep_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorldPayload(_message.Message):
    __slots__ = ("get_location", "get_redstone_inputs", "get_redstone_outputs", "ring_bell", "set_all_redstone_outputs", "set_redstone_output", "sleep")
    GET_LOCATION_FIELD_NUMBER: _ClassVar[int]
    GET_REDSTONE_INPUTS_FIELD_NUMBER: _ClassVar[int]
    GET_REDSTONE_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    RING_BELL_FIELD_NUMBER: _ClassVar[int]
    SET_ALL_REDSTONE_OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    SET_REDSTONE_OUTPUT_FIELD_NUMBER: _ClassVar[int]
    SLEEP_FIELD_NUMBER: _ClassVar[int]
    get_location: _get_location_pb2.GetLocation
    get_redstone_inputs: _get_redstone_inputs_pb2.GetRedstoneInputs
    get_redstone_outputs: _get_redstone_outputs_pb2.GetRedstoneOutputs
    ring_bell: _ring_bell_pb2.RingBell
    set_all_redstone_outputs: _set_all_redstone_outputs_pb2.SetAllRedstoneOutputs
    set_redstone_output: _set_redstone_output_pb2.SetRedstoneOutput
    sleep: _sleep_pb2.Sleep
    def __init__(self, get_location: _Optional[_Union[_get_location_pb2.GetLocation, _Mapping]] = ..., get_redstone_inputs: _Optional[_Union[_get_redstone_inputs_pb2.GetRedstoneInputs, _Mapping]] = ..., get_redstone_outputs: _Optional[_Union[_get_redstone_outputs_pb2.GetRedstoneOutputs, _Mapping]] = ..., ring_bell: _Optional[_Union[_ring_bell_pb2.RingBell, _Mapping]] = ..., set_all_redstone_outputs: _Optional[_Union[_set_all_redstone_outputs_pb2.SetAllRedstoneOutputs, _Mapping]] = ..., set_redstone_output: _Optional[_Union[_set_redstone_output_pb2.SetRedstoneOutput, _Mapping]] = ..., sleep: _Optional[_Union[_sleep_pb2.Sleep, _Mapping]] = ...) -> None: ...

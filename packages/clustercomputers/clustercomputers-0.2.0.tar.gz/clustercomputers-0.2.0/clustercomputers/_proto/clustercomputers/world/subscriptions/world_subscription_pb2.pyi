from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class WorldSubscription(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORLD_SUBSCRIPTION_UNSPECIFIED: _ClassVar[WorldSubscription]
    WORLD_SUBSCRIPTION_REDSTONE_UPDATE: _ClassVar[WorldSubscription]
WORLD_SUBSCRIPTION_UNSPECIFIED: WorldSubscription
WORLD_SUBSCRIPTION_REDSTONE_UPDATE: WorldSubscription

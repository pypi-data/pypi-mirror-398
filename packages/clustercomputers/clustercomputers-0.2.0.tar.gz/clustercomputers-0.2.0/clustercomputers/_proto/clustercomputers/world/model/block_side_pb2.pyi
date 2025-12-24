from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class BlockSide(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BLOCK_SIDE_UNSPECIFIED: _ClassVar[BlockSide]
    BLOCK_SIDE_FRONT: _ClassVar[BlockSide]
    BLOCK_SIDE_BACK: _ClassVar[BlockSide]
    BLOCK_SIDE_LEFT: _ClassVar[BlockSide]
    BLOCK_SIDE_RIGHT: _ClassVar[BlockSide]
    BLOCK_SIDE_TOP: _ClassVar[BlockSide]
    BLOCK_SIDE_BOTTOM: _ClassVar[BlockSide]
BLOCK_SIDE_UNSPECIFIED: BlockSide
BLOCK_SIDE_FRONT: BlockSide
BLOCK_SIDE_BACK: BlockSide
BLOCK_SIDE_LEFT: BlockSide
BLOCK_SIDE_RIGHT: BlockSide
BLOCK_SIDE_TOP: BlockSide
BLOCK_SIDE_BOTTOM: BlockSide

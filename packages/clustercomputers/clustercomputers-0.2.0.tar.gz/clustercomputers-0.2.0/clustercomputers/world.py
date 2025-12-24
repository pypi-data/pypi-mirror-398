__all__ = (
    "BlockLocation",
    "BlockLocation",
    "BlockPosition",
    "BlockSide",
    "CardinalDirection",
    "RedstoneSides",
    "SideRedstoneSignal",
    "WorldActionId",
)

import dataclasses
import enum
from collections.abc import Iterable, Iterator

from ._proto.clustercomputers.world.actions import world_action_id_pb2
from ._proto.clustercomputers.world.model import (
    block_location_pb2,
    block_position_pb2,
    block_side_pb2,
    cardinal_direction_pb2,
    redstone_sides_pb2,
    redstone_signal_pb2,
    side_redstone_signal_pb2,
)


@dataclasses.dataclass(frozen=True)
class BlockPosition:
    """Coordinates of a block in the world"""

    x: int
    y: int
    z: int

    @staticmethod
    def _from_proto(
        proto: block_position_pb2.BlockPosition,
    ) -> "BlockPosition":
        return BlockPosition(x=proto.x, y=proto.y, z=proto.z)


class BlockSide(enum.Enum):
    """Relative sides of a block"""

    FRONT = enum.auto()
    BACK = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    TOP = enum.auto()
    BOTTOM = enum.auto()

    @staticmethod
    def _from_proto(proto: block_side_pb2.BlockSide) -> "BlockSide":
        match proto:
            case block_side_pb2.BLOCK_SIDE_FRONT:
                return BlockSide.FRONT
            case block_side_pb2.BLOCK_SIDE_BACK:
                return BlockSide.BACK
            case block_side_pb2.BLOCK_SIDE_LEFT:
                return BlockSide.LEFT
            case block_side_pb2.BLOCK_SIDE_RIGHT:
                return BlockSide.RIGHT
            case block_side_pb2.BLOCK_SIDE_TOP:
                return BlockSide.TOP
            case block_side_pb2.BLOCK_SIDE_BOTTOM:
                return BlockSide.BOTTOM
            case _:
                raise ValueError(proto)

    def _to_proto(self) -> block_side_pb2.BlockSide:
        match self:
            case BlockSide.FRONT:
                return block_side_pb2.BLOCK_SIDE_FRONT
            case BlockSide.BACK:
                return block_side_pb2.BLOCK_SIDE_BACK
            case BlockSide.LEFT:
                return block_side_pb2.BLOCK_SIDE_LEFT
            case BlockSide.RIGHT:
                return block_side_pb2.BLOCK_SIDE_RIGHT
            case BlockSide.TOP:
                return block_side_pb2.BLOCK_SIDE_TOP
            case BlockSide.BOTTOM:
                return block_side_pb2.BLOCK_SIDE_BOTTOM


class CardinalDirection(enum.Enum):
    """Cardinal directions"""

    NORTH = enum.auto()
    SOUTH = enum.auto()
    EAST = enum.auto()
    WEST = enum.auto()

    @staticmethod
    def _from_proto(
        proto: cardinal_direction_pb2.CardinalDirection,
    ) -> "CardinalDirection":
        match proto:
            case cardinal_direction_pb2.CARDINAL_DIRECTION_NORTH:
                return CardinalDirection.NORTH
            case cardinal_direction_pb2.CARDINAL_DIRECTION_SOUTH:
                return CardinalDirection.SOUTH
            case cardinal_direction_pb2.CARDINAL_DIRECTION_EAST:
                return CardinalDirection.EAST
            case cardinal_direction_pb2.CARDINAL_DIRECTION_WEST:
                return CardinalDirection.WEST
            case _:
                raise ValueError(proto)


@dataclasses.dataclass(frozen=True)
class BlockLocation:
    """Location info of a block in the world"""

    dimension: str
    """Dimension, e.g. *minecraft:overworld*"""
    position: BlockPosition
    """Coordinates"""
    facing: CardinalDirection
    """Direction the block is facing"""

    @staticmethod
    def _from_proto(
        proto: block_location_pb2.BlockLocation,
    ) -> "BlockLocation":
        return BlockLocation(
            dimension=proto.dimension,
            position=BlockPosition._from_proto(proto.position),
            facing=CardinalDirection._from_proto(proto.facing),
        )


@dataclasses.dataclass(frozen=True)
class SideRedstoneSignal:
    """Redstone signal on the side of a block

    This can be used for both the *input* (signal received by the block)
    and the *output* (signal emitted by the block)
    """

    side: BlockSide
    strength: int

    @staticmethod
    def _from_proto(
        proto: side_redstone_signal_pb2.SideRedstoneSignal,
    ) -> "SideRedstoneSignal":
        return SideRedstoneSignal(
            side=BlockSide._from_proto(proto.side),
            strength=proto.signal.strength,
        )

    def _to_proto(self) -> side_redstone_signal_pb2.SideRedstoneSignal:
        return side_redstone_signal_pb2.SideRedstoneSignal(
            side=self.side._to_proto(),
            signal=redstone_signal_pb2.RedstoneSignal(strength=self.strength),
        )


@dataclasses.dataclass(frozen=True)
class RedstoneSides(Iterable[SideRedstoneSignal]):
    """Redstone signal on all sides of a block

    This can be used for both the *inputs* (signals received by the
    block) and the *outputs* (signals emitted by the block)
    """

    front: int = 0
    back: int = 0
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0

    @staticmethod
    def with_all(strength: int) -> "RedstoneSides":
        """Returns RedstoneSides with the same ``strength`` set on all
        sides"""
        return RedstoneSides(
            strength, strength, strength, strength, strength, strength
        )

    def __iter__(self) -> Iterator[SideRedstoneSignal]:
        """Iterates over all sides"""
        return iter(
            (
                SideRedstoneSignal(BlockSide.FRONT, self.front),
                SideRedstoneSignal(BlockSide.BACK, self.back),
                SideRedstoneSignal(BlockSide.LEFT, self.left),
                SideRedstoneSignal(BlockSide.RIGHT, self.right),
                SideRedstoneSignal(BlockSide.TOP, self.top),
                SideRedstoneSignal(BlockSide.BOTTOM, self.bottom),
            )
        )

    @staticmethod
    def _from_proto(
        proto: redstone_sides_pb2.RedstoneSides,
    ) -> "RedstoneSides":
        return RedstoneSides(
            front=proto.front.strength,
            back=proto.back.strength,
            left=proto.left.strength,
            right=proto.right.strength,
            top=proto.top.strength,
            bottom=proto.bottom.strength,
        )

    def _to_proto(self) -> redstone_sides_pb2.RedstoneSides:
        return redstone_sides_pb2.RedstoneSides(
            front=redstone_signal_pb2.RedstoneSignal(strength=self.front),
            back=redstone_signal_pb2.RedstoneSignal(strength=self.back),
            left=redstone_signal_pb2.RedstoneSignal(strength=self.left),
            right=redstone_signal_pb2.RedstoneSignal(strength=self.right),
            top=redstone_signal_pb2.RedstoneSignal(strength=self.top),
            bottom=redstone_signal_pb2.RedstoneSignal(strength=self.bottom),
        )


@dataclasses.dataclass(frozen=True)
class WorldActionId:
    """ID of a WorldAction that was submitted to the Minecraft server

    This is normally handled internally by the clients, but it's
    included in logs and exceptions to help with troubleshooting.
    """

    id: int

    @staticmethod
    def _from_proto(
        proto: world_action_id_pb2.WorldActionId,
    ) -> "WorldActionId":
        return WorldActionId(id=proto.id)

    def _to_proto(self) -> world_action_id_pb2.WorldActionId:
        return world_action_id_pb2.WorldActionId(id=self.id)


type _WorldResultValue = BlockLocation | RedstoneSides | None
"""Union of possible value types in a successful WorldResult"""


class _WorldResultValueType(enum.Enum):
    """Enum of WorldResultValue types with their field name"""

    NO_VALUE = None
    BLOCK_LOCATION = "block_location"
    REDSTONE_SIDES = "redstone_sides"

    field_name: str | None
    """Name of the protobuf field in ``WorldResult.Value``, or ``None``
    if the result should have no return value"""

    def __init__(self, field_name: str | None) -> None:
        self.field_name = field_name

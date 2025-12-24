__all__ = (
    "AsyncBatchSoundService",
    "AsyncSoundService",
    "SyncBatchSoundService",
    "SyncSoundService",
)

from typing import TYPE_CHECKING

from ._proto.clustercomputers.world.actions.ring_bell_pb2 import (
    RingBell as pb_RingBell,
)
from ._proto.clustercomputers.world.actions.world_payload_pb2 import (
    WorldPayload as pb_WorldPayload,
)
from .world import _WorldResultValueType

if TYPE_CHECKING:
    from .aclient import AsyncBatch, AsyncBatchFuture, AsyncClient
    from .sclient import SyncBatch, SyncBatchFuture, SyncClient


class SyncSoundService:
    """Sync service that can be used to play sounds

    This class should not be created directly. Use
    :attr:`SyncClient.sound`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "SyncClient") -> None:
        self._client = _client

    def ring_bell(self) -> None:
        """Plays a bell sound

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(ring_bell=pb_RingBell())
        self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )


class SyncBatchSoundService:
    """Sync batch service that can be used to play sounds

    This class should not be created directly. Use
    :attr:`SyncBatch.sound`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "SyncBatch") -> None:
        self._batch = _batch

    def ring_bell(self) -> "SyncBatchFuture[None]":
        """Plays a bell sound"""
        payload = pb_WorldPayload(ring_bell=pb_RingBell())
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )


class AsyncSoundService:
    """Async service that can be used to play sounds

    This class should not be created directly. Use
    :attr:`AsyncClient.sound`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "AsyncClient") -> None:
        self._client = _client

    async def ring_bell(self) -> None:
        """Plays a bell sound

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(ring_bell=pb_RingBell())
        await self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )


class AsyncBatchSoundService:
    """Async batch service that can be used to play sounds

    This class should not be created directly. Use
    :attr:`AsyncBatch.sound`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "AsyncBatch") -> None:
        self._batch = _batch

    def ring_bell(self) -> "AsyncBatchFuture[None]":
        """Plays a bell sound"""
        payload = pb_WorldPayload(ring_bell=pb_RingBell())
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )

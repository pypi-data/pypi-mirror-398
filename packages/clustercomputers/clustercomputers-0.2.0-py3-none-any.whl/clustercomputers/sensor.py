__all__ = (
    "AsyncBatchSensorService",
    "AsyncSensorService",
    "SyncBatchSensorService",
    "SyncSensorService",
)

from typing import TYPE_CHECKING

from ._proto.clustercomputers.world.actions.get_location_pb2 import (
    GetLocation as pb_GetLocation,
)
from ._proto.clustercomputers.world.actions.world_payload_pb2 import (
    WorldPayload as pb_WorldPayload,
)
from .world import BlockLocation, _WorldResultValueType

if TYPE_CHECKING:
    from .aclient import AsyncBatch, AsyncBatchFuture, AsyncClient
    from .sclient import SyncBatch, SyncBatchFuture, SyncClient


class SyncSensorService:
    """Sync service that can be used to get misc info

    This class should not be created directly. Use
    :attr:`SyncClient.sensor`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "SyncClient") -> None:
        self._client = _client

    def get_location(self) -> BlockLocation:
        """Gets the location info, including the coordinates and the
        direction the computer is facing

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(get_location=pb_GetLocation())
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.BLOCK_LOCATION, payload
        )
        assert isinstance(result, BlockLocation)
        return result


class SyncBatchSensorService:
    """Sync batch service that can be used to get misc info

    This class should not be created directly. Use
    :attr:`SyncBatch.sensor`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "SyncBatch") -> None:
        self._batch = _batch

    def get_location(self) -> "SyncBatchFuture[BlockLocation]":
        """Gets the location data, including the coordinates and the
        direction the computer is facing"""
        payload = pb_WorldPayload(get_location=pb_GetLocation())
        return self._batch._create_future(
            _WorldResultValueType.BLOCK_LOCATION, payload
        )


class AsyncSensorService:
    """Async service that can be used to get misc info

    This class should not be created directly. Use
    :attr:`AsyncClient.sensor`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "AsyncClient") -> None:
        self._client = _client

    async def get_location(self) -> BlockLocation:
        """Gets the location info, including the coordinates and the
        direction the computer is facing

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(get_location=pb_GetLocation())
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.BLOCK_LOCATION, payload
        )
        assert isinstance(result, BlockLocation)
        return result


class AsyncBatchSensorService:
    """Async batch service that can be used to get misc info

    This class should not be created directly. Use
    :attr:`AsyncBatch.sensor`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "AsyncBatch") -> None:
        self._batch = _batch

    def get_location(self) -> "AsyncBatchFuture[BlockLocation]":
        """Gets the location data, including the coordinates and the
        direction the computer is facing"""
        payload = pb_WorldPayload(get_location=pb_GetLocation())
        return self._batch._create_future(
            _WorldResultValueType.BLOCK_LOCATION, payload
        )

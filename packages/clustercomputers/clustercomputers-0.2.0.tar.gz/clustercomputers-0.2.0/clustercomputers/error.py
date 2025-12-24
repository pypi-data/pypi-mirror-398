__all__ = (
    "CancelledError",
    "ClusterComputersError",
    "CommunicationError",
    "ComputerTimeoutError",
    "WorldActionFailedError",
)

from .world import WorldActionId


class ClusterComputersError(Exception):
    """Base exception for all ClusterComputers errors"""

    __slots__ = ()


class CommunicationError(ClusterComputersError):
    """Exception raised when a communication/network error occurs with
    the podinterface"""

    __slots__ = ()


class WorldActionFailedError(ClusterComputersError):
    """Exception raised when a WorldAction fails on the Minecraft
    server"""

    __slots__ = ("failure_message", "payload_index", "world_id")

    world_id: WorldActionId
    """ID of the WorldAction"""
    payload_index: int
    """Index of the WorldPayload that caused the failure, starting from
    0"""
    failure_message: str
    """Message from the Minecraft server explaining why the action
    failed"""

    def __init__(
        self, world_id: WorldActionId, payload_index: int, failure_message: str
    ) -> None:
        super().__init__(world_id, payload_index, failure_message)
        self.world_id = world_id
        self.payload_index = payload_index
        self.failure_message = failure_message

    def __str__(self) -> str:
        return (
            f"id={self.world_id.id}, index={self.payload_index}: "
            f"{self.failure_message}"
        )


class CancelledError(ClusterComputersError):
    """Exception raised by the :class:`clustercomputers.SyncClient` in
    order to cancel methods that are currently running when the client
    is closed

    This is only used by the sync classes. The async classes use
    standard asyncio cancellations.
    """

    __slots__ = ()


class ComputerTimeoutError(ClusterComputersError):
    """Exception raised when a :class:`clustercomputers.SyncBatchFuture`
    times out while waiting for an action to complete"""

    __slots__ = ()

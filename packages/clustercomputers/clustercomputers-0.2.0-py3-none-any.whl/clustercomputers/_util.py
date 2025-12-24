import base64
import dataclasses
import enum
import logging
import os
import threading
from collections.abc import Iterable

from ._proto.clustercomputers.world.actions import world_result_pb2
from ._proto.clustercomputers.world.rpc.stream_world_action_status_response_pb2 import (
    StreamWorldActionStatusResponse as pb_StreamWorldActionStatusResponse,
)
from ._proto.clustercomputers.world.subscriptions import (
    world_subscription_update_pb2,
)
from .error import CommunicationError, WorldActionFailedError
from .world import (
    BlockLocation,
    RedstoneSides,
    WorldActionId,
    _WorldResultValue,
    _WorldResultValueType,
)

_logger = logging.getLogger(__name__)


class ContextState(enum.Enum):
    """State of a context manager"""

    NEW = enum.auto()
    ENTERED = enum.auto()
    EXITED = enum.auto()


class ThreadNamer:
    """Generate unique, descriptive names that can be used as the name
    of a thread or async task

    Example names::

        clustercomputers-name-1
        clustercomputers-name-2

    :param name: Base name of the thread/task
    :param thread_safe: Whether this instance should be thread-safe. Set
        this to ``False`` for async code because it uses a blocking lock
    """

    __slots__ = ("_count", "_lock", "_name")

    def __init__(self, name: str, *, thread_safe: bool) -> None:
        self._name = name
        self._count = 1
        self._lock = threading.Lock() if thread_safe else None

    def next(self) -> str:
        """Returns the next unique name for a thread/task"""
        count = self._get_and_increment()
        full_name = f"clustercomputers-{self._name}-{count}"
        return full_name

    def _get_and_increment(self) -> int:
        if self._lock is None:
            count = self._count
            self._count += 1
        else:
            with self._lock:
                count = self._count
                self._count += 1

        return count


@dataclasses.dataclass(frozen=True)
class ConnectParams:
    """Params for connecting to the computer's podinterface"""

    address: str
    user: str
    password: str = dataclasses.field(repr=False)

    @staticmethod
    def supplement_env(
        address: str | None, user: str | None, password: str | None
    ) -> "ConnectParams":
        """Supplements the given params with the values from the
        computer's env vars

        If any of the params are ``None``, they will be loaded from the
        environment.
        """
        return ConnectParams(
            address=load_missing_env(
                "CLUSTERCOMPUTERS_INTERFACE_ADDRESS", address
            ),
            user=load_missing_env("CLUSTERCOMPUTERS_INTERFACE_USERNAME", user),
            password=load_missing_env(
                "CLUSTERCOMPUTERS_INTERFACE_PASSWORD", password
            ),
        )


def load_missing_env(key: str, value: str | None) -> str:
    """Returns the ``value`` if it's not ``None``, otherwise loads the
    value from the env var corresponding to the ``key``"""
    if value is not None:
        return value

    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing env var: {key}")
    return value


def build_basic_auth_metadatum(params: ConnectParams) -> tuple[str, str]:
    """Builds the basic auth metadatum (header) for the ``params``"""
    encoded = base64.b64encode(
        f"{params.user}:{params.password}".encode("utf-8")
    )
    # Metadata keys must be lowercase
    return ("authorization", f"Basic {encoded.decode('utf-8')}")


def check_and_get_world_result_type(
    expected_type: _WorldResultValueType,
    world_id: WorldActionId,
    payload_index: int,
    result: world_result_pb2.WorldResult,
) -> _WorldResultValue:
    """Verifies that a WorldResult succeeded and has the expected value
    type, then converts the value to a native dataclass

    :raises WorldActionFailedError: if the payload failed
    :raises CommunicationError: if the result has the wrong value type
        (bug)
    """
    if not result.HasField("value"):
        raise WorldActionFailedError(
            world_id, payload_index, result.failure_message
        )
    value = result.value

    field_name: str | None = value.WhichOneof("value")
    if field_name != expected_type.field_name:
        raise CommunicationError(
            "WorldResult has unexpected value type: "
            f"{expected_type=}, {world_id=}, {result=}"
        )

    match field_name:
        case None:
            return None
        case _WorldResultValueType.BLOCK_LOCATION.field_name:
            return BlockLocation._from_proto(value.block_location)
        case _WorldResultValueType.REDSTONE_SIDES.field_name:
            return RedstoneSides._from_proto(value.redstone_sides)
        case _:
            raise ValueError(f"Unknown WorldResult value type: {type(value)}")


def check_world_sub_type(
    expected_field: str,
    update: world_subscription_update_pb2.WorldSubscriptionUpdate,
) -> None:
    """Verifies that a WorldSubscriptionUpdate has the expected type"""
    if not update.HasField(expected_field):
        raise CommunicationError(
            "WorldSubscriptionUpdate has unexpected type: "
            f"{expected_field=}, {update=}"
        )


class WorldActionStatusResultStreamer:
    """Helper class for processing responses from a
    StreamWorldActionStatus call"""

    __slots__ = "_got_initial_status"

    def __init__(self) -> None:
        self._got_initial_status = False

    @property
    def got_initial_status(self) -> bool:
        return self._got_initial_status

    def process(
        self, response: pb_StreamWorldActionStatusResponse
    ) -> Iterable[world_result_pb2.WorldResult]:
        _logger.debug("Got WorldAction status: %s", response)
        if not self._got_initial_status:
            self._got_initial_status = True
            return self._process_initial_status(response)
        else:
            return self._process_payload_processed(response)

    def _process_initial_status(
        self, response: pb_StreamWorldActionStatusResponse
    ) -> Iterable[world_result_pb2.WorldResult]:
        if not response.HasField("initial_status"):
            raise CommunicationError(
                "StreamWorldActionStatus response has unexpected field: "
                f"expected=initial_status, {response=}"
            )

        return response.initial_status.results

    def _process_payload_processed(
        self, response: pb_StreamWorldActionStatusResponse
    ) -> Iterable[world_result_pb2.WorldResult]:
        if not response.HasField("payload_processed"):
            raise CommunicationError(
                "StreamWorldActionStatus response has unexpected field: "
                f"expected=payload_processed, {response=}"
            )

        return (response.payload_processed,)

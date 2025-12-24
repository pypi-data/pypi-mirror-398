__all__ = ("SyncBatch", "SyncBatchFuture", "SyncClient", "connect")

import enum
import logging
import threading
from collections.abc import (
    Callable,
    Collection,
    Generator,
    Iterable,
    Sequence,
)
from types import TracebackType
from typing import TYPE_CHECKING, Any, Final, Literal, Self

import grpc

from ._proto.clustercomputers.world.actions.sleep_pb2 import Sleep as pb_Sleep
from ._proto.clustercomputers.world.actions.world_payload_pb2 import (
    WorldPayload as pb_WorldPayload,
)
from ._proto.clustercomputers.world.actions.world_result_pb2 import (
    WorldResult as pb_WorldResult,
)
from ._proto.clustercomputers.world.rpc.create_world_action_request_pb2 import (
    CreateWorldActionRequest as pb_CreateWorldActionRequest,
)
from ._proto.clustercomputers.world.rpc.create_world_action_response_pb2 import (
    CreateWorldActionResponse as pb_CreateWorldActionResponse,
)
from ._proto.clustercomputers.world.rpc.pod_world_service_pb2_grpc import (
    PodWorldServiceStub as pb_PodWorldServiceStub,
)
from ._proto.clustercomputers.world.rpc.stream_world_action_status_request_pb2 import (
    StreamWorldActionStatusRequest as pb_StreamWorldActionStatusRequest,
)
from ._proto.clustercomputers.world.rpc.stream_world_action_status_response_pb2 import (
    StreamWorldActionStatusResponse as pb_StreamWorldActionStatusResponse,
)
from ._proto.clustercomputers.world.rpc.subscribe_world_subscription_updates_request_pb2 import (
    SubscribeWorldSubscriptionUpdatesRequest as pb_SubscribeWorldSubscriptionUpdatesRequest,
)
from ._proto.clustercomputers.world.rpc.subscribe_world_subscription_updates_response_pb2 import (
    SubscribeWorldSubscriptionUpdatesResponse as pb_SubscribeWorldSubscriptionUpdatesResponse,
)
from ._proto.clustercomputers.world.subscriptions.world_subscription_pb2 import (
    WorldSubscription as pb_WorldSubscription,
)
from ._proto.clustercomputers.world.subscriptions.world_subscription_update_pb2 import (
    WorldSubscriptionUpdate as pb_WorldSubscriptionUpdate,
)
from ._util import (
    ConnectParams,
    ContextState,
    ThreadNamer,
    WorldActionStatusResultStreamer,
    build_basic_auth_metadatum,
    check_and_get_world_result_type,
)
from .error import CancelledError, CommunicationError, ComputerTimeoutError
from .redstone import SyncBatchRedstoneService, SyncRedstoneService
from .sensor import SyncBatchSensorService, SyncSensorService
from .sound import SyncBatchSoundService, SyncSoundService
from .world import (
    WorldActionId,
    _WorldResultValue,
    _WorldResultValueType,
)

_logger: Final = logging.getLogger(__name__)

if TYPE_CHECKING:

    class _GrpcCall[T](Iterable[T], grpc.Call, grpc.Future[T]):
        """Type hint for the value returned by gRPC unary future and
        server-streaming calls

        The calls actually return
        :class:`grpc._channel._MultiThreadedRendezvous`, but we can't
        use this class directly because it's private and isn't generic.
        This class is just a recreation of it that's good enough for our
        use case.
        """

        pass


def connect(
    *,
    address: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> "SyncClient":
    """Connects to the ClusterComputer podinterface and creates a new
    :class:`SyncClient`

    All params are optional when running in the computer container. They
    will be auto-detected from the environment.

    This may be used as a context manager if you want to make sure that
    all resources are cleaned up when it's no longer needed. For
    example::

        with cc.connect() as client:
            location = client.sensor.get_location()

    For async code, use :func:`clustercomputers.async_connect`.

    :param address: Address of the podinterface, e.g. *localhost:9810*
    :param user: Basic auth username
    :param password: Basic auth password
    """
    connect_params = ConnectParams.supplement_env(address, user, password)
    _logger.debug("Connecting with params: %s", connect_params)
    auth_header = build_basic_auth_metadatum(connect_params)

    # The channel is lazy-loaded; it won't throw connection errors until
    # we actually try to use it
    channel = grpc.insecure_channel(connect_params.address)
    return SyncClient(channel, close_channel=True, metadata=(auth_header,))


class SyncClient:
    """Client for interacting with the Minecraft server synchronously

    Creating this class directly isn't recommended. Use
    :func:`connect` instead.

    This class may be used as a context manager if you want to make sure
    that all resources are cleaned up when it's no longer needed.

    This class is thread-safe.

    For async code, use :class:`clustercomputers.AsyncClient`.

    :param channel: gRPC channel of the podinterface.
    :param close_channel: Whether to close the gRPC channel when this
        class is closed. If ``False``, the caller must close the channel
        themselves.
    :param metadata: Extra metadata (headers) that will be added to
        every request. This can be used for auth.
    """

    __slots__ = (
        "_channel",
        "_close_channel",
        "_closed",
        "_futures",
        "_lock",
        "_metadata",
        "_redstone",
        "_sensor",
        "_sound",
        "_stub",
    )

    def __init__(
        self,
        channel: grpc.Channel,
        *,
        close_channel: bool = False,
        metadata: Sequence[tuple[str, str]] = (),
    ) -> None:
        self._channel = channel
        self._close_channel = close_channel
        self._metadata = tuple(metadata)

        self._stub = pb_PodWorldServiceStub(channel)  # type: ignore[no-untyped-call]
        self._closed = False
        self._lock = threading.RLock()
        self._futures: set["grpc.Future[Any]"] = set()

        self._redstone = SyncRedstoneService(_client=self)
        self._sensor = SyncSensorService(_client=self)
        self._sound = SyncSoundService(_client=self)

    @property
    def closed(self) -> bool:
        """Returns ``True`` if this client is closed

        The client is considered to be closed if the context manager has
        exited, or if :meth:`close` was called.
        """
        return self._closed

    @property
    def redstone(self) -> SyncRedstoneService:
        """Returns a service that can be used to interact with
        redstone"""
        return self._redstone

    @property
    def sensor(self) -> SyncSensorService:
        """Returns a service that can be used to get misc info"""
        return self._sensor

    @property
    def sound(self) -> SyncSoundService:
        """Returns a service that can be used to play sound"""
        return self._sound

    def _check_not_closed(self) -> None:
        if self.closed:
            raise CancelledError()

    def __enter__(self) -> Self:
        self._check_not_closed()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Closes the client

        See :meth:`close` for details.
        """
        self.close()
        return False

    def close(self) -> None:
        """Closes the client

        Any calls that are currently being made by other threads will be
        cancelled, causing them to throw a :class:`CancelledError`.

        If the client is already closed, this will have no effect.

        This will be called automatically when the client is used as a
        context manager, but you can also call it manually if you want
        to cancel all running calls. For example, you could call this in
        a signal handler if you want to exit the program.

        This will also close the channel if ``close_channel`` was set to
        ``True`` when you created this class.

        You can use :attr:`closed` to check if the client has been
        closed.
        """
        with self._lock:
            if self._closed:
                # Already closed
                return
            self._closed = True

            # Copy this to avoid races with `_discard_future()`
            futures = self._futures.copy()

        _logger.info("Closing SyncClient")
        for future in futures:
            future.cancel()

        if self._close_channel:
            _logger.debug("Closing channel")
            self._channel.close()

    def _add_future(self, future: "grpc.Future[Any]") -> None:
        """Adds the future to the set so that it will be cancelled if
        the client is closed

        This must be called within a lock that also creates the future.
        Otherwise, we might miss futures due to race conditions if
        :meth:`close` is currently running.

        :raises CancelledError: if the client is closed
        """
        self._check_not_closed()
        self._futures.add(future)
        future.add_done_callback(self._discard_future)

    def _discard_future(self, future: "grpc.Future[Any]") -> None:
        with self._lock:
            self._futures.discard(future)

    def _create_world_action(
        self, payloads: Sequence[pb_WorldPayload]
    ) -> WorldActionId:
        _logger.info("Creating WorldAction with payloads: %s", payloads)
        request = pb_CreateWorldActionRequest(payloads=payloads)

        with self._lock:
            call: _GrpcCall[pb_CreateWorldActionResponse] = (
                self._stub.CreateWorldAction.future(
                    request, metadata=self._metadata
                )
            )
            self._add_future(call)

        try:
            response = call.result()
        except grpc.FutureCancelledError as e:
            raise CancelledError() from e
        except grpc.RpcError as e:
            if e.code() is grpc.StatusCode.CANCELLED:
                raise CancelledError() from e

            raise CommunicationError(
                f"Error creating WorldAction: {request=}"
            ) from e

        world_id = WorldActionId._from_proto(response.id)
        _logger.info("Got WorldActionId: %s", world_id)
        return world_id

    def _stream_world_results(
        self, world_id: WorldActionId
    ) -> Generator[pb_WorldResult]:
        request = pb_StreamWorldActionStatusRequest(id=world_id._to_proto())
        with self._lock:
            response_stream: _GrpcCall[pb_StreamWorldActionStatusResponse] = (
                self._stub.StreamWorldActionStatus(
                    request, metadata=self._metadata
                )
            )
            self._add_future(response_stream)

        _logger.debug("Streaming WorldAction status")
        streamer = WorldActionStatusResultStreamer()

        try:
            for response in response_stream:
                yield from streamer.process(response)
        except grpc.FutureCancelledError as e:
            raise CancelledError() from e
        except grpc.RpcError as e:
            if e.code() is grpc.StatusCode.CANCELLED:
                raise CancelledError() from e

            raise CommunicationError(
                f"Error streaming WorldAction status: {request=}"
            ) from e
        finally:
            # Cancel the call when the generator is closed
            response_stream.cancel()

        _logger.debug("Finished streaming WorldAction status")
        if not streamer.got_initial_status:
            raise CommunicationError(
                "WorldAction status stream returned no responses"
            )

    def _create_and_get_single_world_action(
        self, expected_type: _WorldResultValueType, payload: pb_WorldPayload
    ) -> _WorldResultValue:
        self._check_not_closed()
        world_id = self._create_world_action((payload,))

        results = tuple(self._stream_world_results(world_id))
        if len(results) != 1:
            raise CommunicationError(
                "WorldAction has unexpected number of WorldPayloads. "
                f"expected=1, actual={len(results)}, {world_id=}, {results=}"
            )

        result = results[0]
        return check_and_get_world_result_type(
            expected_type, world_id, 0, result
        )

    def _subscribe_world_subs(
        self, subscriptions: Collection[pb_WorldSubscription]
    ) -> Generator[pb_WorldSubscriptionUpdate]:
        self._check_not_closed()

        if _logger.isEnabledFor(logging.INFO):
            _logger.info(
                "Subscribing to WorldSubscriptions: %s",
                [pb_WorldSubscription.Name(sub) for sub in subscriptions],
            )

        request = pb_SubscribeWorldSubscriptionUpdatesRequest(
            subscriptions=subscriptions
        )
        with self._lock:
            response_stream: _GrpcCall[
                pb_SubscribeWorldSubscriptionUpdatesResponse
            ] = self._stub.SubscribeWorldSubscriptionUpdates(
                request, metadata=self._metadata
            )
            self._add_future(response_stream)

        try:
            for response in response_stream:
                _logger.debug(
                    "Got WorldSubscriptionUpdate: %s", response.update
                )
                yield response.update
        except grpc.FutureCancelledError:
            raise CancelledError()
        except grpc.RpcError as e:
            if e.code() is grpc.StatusCode.CANCELLED:
                raise CancelledError() from e

            raise CommunicationError(
                "Error while subscribed to WorldSubscriptionUpdates: "
                f"{request=}"
            ) from e
        finally:
            # Cancel the call when the generator is closed
            response_stream.cancel()

        raise RuntimeError("WorldSubscription loop ended unexpectedly")

    def batch(self, *, wait: bool = True) -> "SyncBatch":
        """Creates a new batch of payloads

        See :class:`SyncBatch` for details.

        :raises CancelledError: if this client is closed
        """
        self._check_not_closed()
        return SyncBatch(_client=self, _wait=wait)


class _FutureState(enum.Enum):
    """State of a :class:`SyncBatchFuture`"""

    PENDING = enum.auto()
    """Future was created, but the batch hasn't been submitted yet"""
    RUNNING = enum.auto()
    """Batch has been submitted, and we're waiting for the result from
    the Minecraft server"""
    SUCCEEDED = enum.auto()
    """Future finished without error"""
    FAILED = enum.auto()
    """Future failed with an exception"""
    CANCELLED = enum.auto()
    """Future was cancelled, i.e. the :class:`SyncClient` was closed"""


class _NoResult(enum.Enum):
    """Singleton used by :class:`SyncBatchFuture` to indicate that the
    result hasn't been received yet"""

    INSTANCE = enum.auto()


# This class intentionally doesn't implement `running()` because we
# don't know when the Minecraft server starts processing the payload.
class SyncBatchFuture[T]:
    """Future that can be used to check the status or retrieve the
    result of a payload that was created by an :class:`SyncBatch`.

    This class is based on :class:`concurrent.futures.Future`, and works
    mostly the same way.

    This class is thread-safe.

    :param [T]: Type of the result
    """

    __slots__ = (
        "_callbacks",
        "_condition",
        "_exception",
        "_payload",
        "_payload_index",
        "_result",
        "_result_type",
        "_state",
    )

    def __init__(
        self,
        *,
        _result_type: _WorldResultValueType,
        _payload_index: int,
        _payload: pb_WorldPayload,
    ) -> None:
        self._result_type = _result_type
        self._payload_index = _payload_index
        self._payload = _payload
        self._state = _FutureState.PENDING
        self._condition = threading.Condition()
        self._result: T | _NoResult = _NoResult.INSTANCE
        self._exception: BaseException | None = None
        self._callbacks: list[Callable[[SyncBatchFuture[T]], object]] = []

    def _check_not_pending(self) -> None:
        if self._state is _FutureState.PENDING:
            raise RuntimeError(
                "Payload results cannot be accessed until the action has been "
                "sent to the Minecraft server (the context manager has exited)"
            )

    def cancelled(self) -> bool:
        """Returns ``True`` if the future was cancelled, i.e. the client
        was closed"""
        return self._state is _FutureState.CANCELLED

    def done(self) -> bool:
        """Returns ``True`` if the future is *done*

        The future is *done* if the payload has completed successfully,
        the payload failed, or the future was cancelled.
        """
        return self._state in {
            _FutureState.SUCCEEDED,
            _FutureState.FAILED,
            _FutureState.CANCELLED,
        }

    def _wait_until_done(self, timeout: float | None) -> None:
        with self._condition:
            if self.done():
                return

            finished = self._condition.wait(timeout)
            if not finished:
                raise ComputerTimeoutError(
                    "Timed out while waiting for payload "
                    f"{self._payload_index} to finish"
                )

    def result(self, timeout: float | None = None) -> T:
        """Waits for the payload to finish, then returns the result

        :param timeout: Number of seconds to wait for the payload to
            finish, or ``None`` to wait forever. If the timeout is
            reached before the payload finishes, a
            :class:`ComputerTimeoutError` will be raised

        :raises WorldActionFailedError: if this payload or a previous
            payload in the action fails
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises RuntimeError: if the action hasn't been sent to the
            server yet
        :raises CancelledError: if the future is cancelled
        :raises ComputerTimeoutError: if the ``timeout`` is reached
            before the payload finishes
        """
        with self._condition:
            self._check_not_pending()
            self._wait_until_done(timeout)

            match self._state:
                case _FutureState.SUCCEEDED:
                    assert self._result is not _NoResult.INSTANCE
                    return self._result
                case _FutureState.FAILED:
                    assert self._exception is not None
                    raise self._exception
                case _FutureState.CANCELLED:
                    raise CancelledError()
                case _:
                    raise AssertionError(self._state)

    def exception(self, timeout: float | None = None) -> BaseException | None:
        """Waits for the payload to finish, then returns the exception
        if it failed, or ``None`` if it succeeded.

        :param timeout: Number of seconds to wait for the payload to
            finish, or ``None`` to wait forever. If the timeout is
            reached before the payload finishes, a
            :class:`ComputerTimeoutError` will be raised

        :raises RuntimeError: if the action hasn't been sent to the
            server yet
        :raises CancelledError: if the future is cancelled
        :raises ComputerTimeoutError: if the ``timeout`` is reached
            before the payload finishes
        """
        with self._condition:
            self._check_not_pending()
            self._wait_until_done(timeout)

            match self._state:
                case _FutureState.SUCCEEDED:
                    return None
                case _FutureState.FAILED:
                    assert self._exception is not None
                    return self._exception
                case _FutureState.CANCELLED:
                    raise CancelledError()
                case _:
                    raise AssertionError(self._state)

    def _call_callback(
        self, fn: Callable[["SyncBatchFuture[T]"], object]
    ) -> None:
        try:
            fn(self)
        except Exception:
            _logger.exception(
                "Callback failed: callback=%s, future=%s", fn, self
            )

    def _call_all_callbacks(self) -> None:
        with self._condition:
            callbacks = self._callbacks
            # Clear the callbacks so we don't keep a reference to them
            # (allows them to be garbage-collected)
            self._callbacks = []

        for callback in callbacks:
            self._call_callback(callback)

    def add_done_callback(
        self, fn: Callable[["SyncBatchFuture[T]"], object]
    ) -> None:
        """Schedules the callback so that it will be run once this
        future is done

        If this future is already done, the callback will be called
        immediately.

        If the same callback is added multiple times, it will be called
        once for each time it was added.

        The callback should return quickly, or other payloads might be
        blocked from finishing.
        """
        with self._condition:
            if not self.done():
                self._callbacks.append(fn)
                return

        # Future already done; call it now
        self._call_callback(fn)

    # This method isn't defined in concurrent.futures, but we added it
    # anyway for parity with AsyncBatchFuture
    def remove_done_callback(
        self, fn: Callable[["SyncBatchFuture[T]"], object]
    ) -> int:
        """Removes a callback that was previously added with
        :meth:`add_done_callback`

        If the callback wasn't previously added, this will have no
        effect.

        :return: The number of callbacks that were removed. Usually this
            is 0 or 1, but it may be greater if the callback was added
            via :meth:`add_done_callback` multiple times
        """
        with self._condition:
            old_count = len(self._callbacks)
            self._callbacks = [c for c in self._callbacks if c != fn]
            new_count = len(self._callbacks)

        return old_count - new_count

    def _start_batch(self) -> None:
        with self._condition:
            if self._state is not _FutureState.PENDING:
                raise RuntimeError("Invalid state")
            self._state = _FutureState.RUNNING

    def _set_result(self, result: T) -> None:
        with self._condition:
            if self._state is not _FutureState.RUNNING:
                raise RuntimeError("Invalid state")

            self._result = result
            self._state = _FutureState.SUCCEEDED
            self._condition.notify_all()

        self._call_all_callbacks()

    def _set_exception(self, exception: BaseException) -> None:
        with self._condition:
            if self._state is not _FutureState.RUNNING:
                raise RuntimeError("Invalid state")

            self._exception = exception
            self._state = _FutureState.FAILED
            self._condition.notify_all()

        self._call_all_callbacks()

    def _cancel(self) -> None:
        with self._condition:
            if self.done():
                return

            self._state = _FutureState.CANCELLED
            self._condition.notify_all()

        self._call_all_callbacks()

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(index={self._payload_index}, "
            f"state={self._state.name}, result={self._result!r}, "
            f"exception={self._exception!r})"
        )


class SyncBatch:
    """Class that's used to synchronously run a batch of tasks on the
    Minecraft server

    This class shouldn't be created directly. Use
    :meth:`SyncClient.batch`.

    This class is thread-safe.

    The batch works by creating a single *action* and sending it to the
    Minecraft server to be processed. Each method in this class adds a
    *payload* (which represents a single task) to the action.

    This class provides the same basic functionality as the methods that
    are available directly in :class:`SyncClient`, but using a batch
    causes the payloads to be submitted to the computer in a single
    network call (as a single action). This ensures that the timing
    between the payloads is consistent, which makes time-sensitive
    tasks such as interacting with redstone more reliable.

    This class must be used as a context manager. For example::

        with client.batch(wait=True) as batch:
            batch.redstone.set_output(cc.BlockSide.RIGHT, 15)
            batch.sleep(20)
            batch.redstone.set_output(cc.BlockSide.RIGHT, 0)

    The action containing all the payloads will be sent to the Minecraft
    server when the context manager exits. The payloads will run on the
    server in sequential order. If any of the payloads fail, the
    remaining payloads won't be run.

    If ``wait`` is ``True``, the context manager will block until the
    action finishes (all payloads have finished). If any of the payloads
    fail, the exception will be raised by the context manager.

    If ``wait`` is ``False``, the context manager will not wait for the
    action to complete before exiting. In this case, you can retrieve
    the results of the payloads in real time. For example::

        with client.batch(wait=False) as batch:
            future1 = batch.sensor.get_location()
            future2 = batch.sleep(20)
            future3 = batch.redstone.get_inputs()

        for future in (future1, future2, future3):
            result = future.result()
            print("Got result:", result)

    If any of the payloads fail, the exception will be raised by the
    future.

    For highly-concurrent programs, consider using
    :class:`clustercomputers.AsyncClient` instead of just setting
    ``wait`` to ``False``.
    """

    __slots__ = (
        "_client",
        "_futures",
        "_lock",
        "_redstone",
        "_sensor",
        "_sound",
        "_state",
        "_wait",
    )

    _THREAD_NAMER: Final = ThreadNamer("batch", thread_safe=True)

    def __init__(self, *, _client: SyncClient, _wait: bool) -> None:
        self._client = _client
        self._wait = _wait
        self._futures: list[SyncBatchFuture[Any]] = []
        self._state = ContextState.NEW
        self._lock = threading.RLock()

        self._redstone = SyncBatchRedstoneService(_batch=self)
        self._sensor = SyncBatchSensorService(_batch=self)
        self._sound = SyncBatchSoundService(_batch=self)

    @property
    def redstone(self) -> SyncBatchRedstoneService:
        """Returns a service that can be used to interact with
        redstone"""
        return self._redstone

    @property
    def sensor(self) -> SyncBatchSensorService:
        """Returns a service that can be used to get misc info"""
        return self._sensor

    @property
    def sound(self) -> SyncBatchSoundService:
        """Returns a service that can be used to play sounds"""
        return self._sound

    def _check_entered(self) -> None:
        if self._state is not ContextState.ENTERED:
            raise RuntimeError(
                "SyncBatch not entered. It must be used as a context manager"
            )

    def __enter__(self) -> Self:
        with self._lock:
            if self._state is not ContextState.NEW:
                raise RuntimeError("SyncBatch already entered")
            self._state = ContextState.ENTERED
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Submits the action with all its payloads to the Minecraft
        server

        If ``wait`` is ``True``, this method will wait until the action
        finishes. Otherwise, the action will be processed in the
        background, and the status of each payload can be accessed from
        the :class:`SyncBatchFuture` objects.

        :raises WorldActionFailedError: if a payload fails (only when
            ``wait`` is ``True``)
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if the client is closed
        """
        with self._lock:
            self._check_entered()
            self._state = ContextState.EXITED

        if len(self._futures) == 0:
            _logger.debug("Batch has no payloads. Aborting")
            return False
        if exc_value is not None:
            _logger.debug("Context raised exception. Aborting")
            self._cancel_remaining_futures()
            return False

        for future in self._futures:
            future._start_batch()

        if self._wait:
            self._run_batch()
        else:
            thread = threading.Thread(
                target=self._run_batch, name=SyncBatch._THREAD_NAMER.next()
            )
            _logger.debug("Starting batch thread: %s", thread.name)
            thread.start()

        return False

    def _run_batch(self) -> None:
        _logger.debug("Running batch")
        try:
            self._run_batch_inner()
        except CancelledError:
            self._cancel_remaining_futures()
            if self._wait:
                # Don't raise if we're not waiting because it causes
                # Python to log an uncaught-exception error
                raise
        except BaseException as e:
            self._propagate_exception(e)

    def _run_batch_inner(self) -> None:
        if self._client.closed:
            raise CancelledError()

        payloads = [future._payload for future in self._futures]
        assert len(payloads) > 0

        world_id = self._client._create_world_action(payloads)
        payload_index = 0

        for result in self._client._stream_world_results(world_id):
            if payload_index >= len(payloads):
                raise CommunicationError(
                    "WorldAction status stream returned too many payloads: "
                    f"expected={len(payloads)}, {world_id=}"
                )

            future = self._futures[payload_index]
            value = check_and_get_world_result_type(
                future._result_type, world_id, payload_index, result
            )
            future._set_result(value)
            payload_index += 1

        if payload_index != len(payloads):
            raise CommunicationError(
                "WorldAction status stream returned too few payloads: "
                f"expected={len(payloads)}, actual={payload_index}, "
                f"{world_id=}"
            )

    def _cancel_remaining_futures(self) -> None:
        _logger.debug("Batch cancelled. Propagating cancellation to futures")
        for future in self._futures:
            future._cancel()

    def _propagate_exception(self, exception: BaseException) -> None:
        """Propagates the exceptions to all unfinished futures, and
        also raises the exception if ``wait`` is ``True`` so that it's
        propagated to the context manager"""
        assert not isinstance(exception, CancelledError)
        _logger.debug(
            "Batch failed. Propagating exception to futures",
            exc_info=exception,
        )

        propagated_exception = False
        for future in self._futures:
            if future.done():
                continue
            future._set_exception(exception)
            propagated_exception = True

        if self._wait:
            # Raise the exception immediately so it's thrown in the
            # context manager
            raise
        elif not propagated_exception:
            # This shouldn't happen. Probably a bug
            _logger.error(
                "Batch failed, but all WorldPayloads have already completed. "
                "Unable to propagate the exception",
                exc_info=exception,
            )

    def _create_future(
        self, result_type: _WorldResultValueType, payload: pb_WorldPayload
    ) -> SyncBatchFuture[Any]:
        with self._lock:
            self._check_entered()

            future: SyncBatchFuture[Any] = SyncBatchFuture(
                _result_type=result_type,
                _payload_index=len(self._futures),
                _payload=payload,
            )
            self._futures.append(future)
            return future

    def sleep(self, ticks: int) -> SyncBatchFuture[None]:
        """Waits for the specified number of game ticks before moving on
        to the next payload

        Note that this uses *game* ticks, not *redstone* ticks. There
        are 20 game ticks in a second, and 2 game ticks equals 1
        redstone tick.
        """
        payload = pb_WorldPayload(sleep=pb_Sleep(ticks=ticks))
        return self._create_future(_WorldResultValueType.NO_VALUE, payload)

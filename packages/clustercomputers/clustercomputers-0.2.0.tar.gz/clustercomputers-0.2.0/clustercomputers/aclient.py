__all__ = ("AsyncBatch", "AsyncBatchFuture", "AsyncClient", "async_connect")

import asyncio
import contextvars
import dataclasses
import logging
from collections.abc import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Collection,
    Generator,
    Sequence,
)
from types import TracebackType
from typing import Any, Final, Literal, Self

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
from .error import CommunicationError
from .redstone import AsyncBatchRedstoneService, AsyncRedstoneService
from .sensor import AsyncBatchSensorService, AsyncSensorService
from .sound import AsyncBatchSoundService, AsyncSoundService
from .world import (
    WorldActionId,
    _WorldResultValue,
    _WorldResultValueType,
)

_logger: Final = logging.getLogger(__name__)


async def async_connect(
    *,
    address: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> "AsyncClient":
    """Connects to the ClusterComputer podinterface and creates a new
    :class:`AsyncClient`

    All params are optional when running in the computer container. They
    will be auto-detected from the environment.

    This may be used as a context manager if you want to make sure that
    all resources are cleaned up when it's no longer needed. For
    example::

        async with await cc.async_connect() as client:
            location = await client.sensor.get_location()

    For non-async code, use :func:`clustercomputers.connect`.

    :param address: Address of the podinterface, e.g. *localhost:9810*
    :param user: Basic auth username
    :param password: Basic auth password
    """
    connect_params = ConnectParams.supplement_env(address, user, password)
    _logger.debug("Connecting with params: %s", connect_params)
    auth_header = build_basic_auth_metadatum(connect_params)

    # The channel is lazy-loaded; it won't throw connection errors until
    # we actually try to use it
    channel = grpc.aio.insecure_channel(connect_params.address)
    return AsyncClient(channel, close_channel=True, metadata=(auth_header,))


class AsyncClient:
    """Client for interacting with the Minecraft server asynchronously

    Creating this class directly isn't recommended. Use
    :func:`async_connect` instead.

    This class may be used as a context manager if you want to make sure
    that all resources are cleaned up when it's no longer needed.

    This class is not thread-safe. It must only be accessed from the
    event loop.

    For non-async code, use :class:`clustercomputers.SyncClient`.

    :param channel: gRPC channel of the podinterface.
    :param close_channel: Whether to close the gRPC channel when this
        class is closed. If ``False``, the caller must close the channel
        themselves.
    :param metadata: Extra metadata (headers) that will be added to
        every request. This can be used for auth.
    """

    __slots__ = (
        "_batch_tasks",
        "_channel",
        "_close_channel",
        "_closed",
        "_metadata",
        "_redstone",
        "_sensor",
        "_sound",
        "_stub",
    )

    _batch_tasks: set[asyncio.Task[None]]
    """Set of tasks that are currently running AsyncBatches

    These are saved in the client so that the tasks don't randomly
    disappear if the user sets ``wait`` to ``False`` and doesn't keep a
    reference to the batch (asyncio only keeps a weakref to tasks).
    """

    def __init__(
        self,
        channel: grpc.aio.Channel,
        *,
        close_channel: bool = False,
        metadata: Sequence[tuple[str, str]] = (),
    ) -> None:
        self._channel = channel
        self._close_channel = close_channel
        self._metadata = tuple(metadata)

        self._stub = pb_PodWorldServiceStub(channel)  # type: ignore[no-untyped-call]
        self._closed = False
        self._batch_tasks = set()

        self._redstone = AsyncRedstoneService(_client=self)
        self._sensor = AsyncSensorService(_client=self)
        self._sound = AsyncSoundService(_client=self)

    @property
    def closed(self) -> bool:
        """Returns ``True`` if this client is closed

        The client is considered to be closed if the context manager has
        exited, or if :meth:`aclose` was called.
        """
        return self._closed

    @property
    def redstone(self) -> AsyncRedstoneService:
        """Returns a service that can be used to interact with
        redstone"""
        return self._redstone

    @property
    def sensor(self) -> AsyncSensorService:
        """Returns a service that can be used to get misc info"""
        return self._sensor

    @property
    def sound(self) -> AsyncSoundService:
        """Returns a service that can be used to play sound"""
        return self._sound

    def _check_not_closed(self) -> None:
        if self.closed:
            raise RuntimeError("AsyncClient is closed")

    async def __aenter__(self) -> Self:
        self._check_not_closed()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Closes the client

        See :meth:`aclose` for details.
        """
        await self.aclose()
        return False

    async def aclose(self) -> None:
        """Closes the client

        If the client is already closed, this will have no effect.

        This will be called automatically when the client is used as a
        context manager, but you can also call it manually.

        This will also close the channel if ``close_channel`` was set to
        ``True`` when you created this class.

        You can use :attr:`closed` to check if the client has been
        closed.
        """
        if self._closed:
            # Already closed
            return
        self._closed = True

        _logger.info("Closing AsyncClient")
        for task in self._batch_tasks:
            task.cancel()
        # Wait for all tasks to finish, ignoring exceptions
        await asyncio.gather(*self._batch_tasks, return_exceptions=True)

        if self._close_channel:
            _logger.debug("Closing channel")
            await self._channel.close()

        _logger.info("Finished closing AsyncClient")

    async def _create_world_action(
        self, payloads: Sequence[pb_WorldPayload]
    ) -> WorldActionId:
        _logger.info("Creating WorldAction with payloads: %s", payloads)
        request = pb_CreateWorldActionRequest(payloads=payloads)

        try:
            response: pb_CreateWorldActionResponse = (
                await self._stub.CreateWorldAction(
                    request, metadata=self._metadata
                )
            )
        except grpc.RpcError as e:
            raise CommunicationError(
                f"Error creating WorldAction: {request=}"
            ) from e

        world_id = WorldActionId._from_proto(response.id)
        _logger.info("Got WorldActionId: %s", world_id)
        return world_id

    async def _stream_world_results(
        self, world_id: WorldActionId
    ) -> AsyncGenerator[pb_WorldResult]:
        request = pb_StreamWorldActionStatusRequest(id=world_id._to_proto())
        response_stream: grpc.aio.UnaryStreamCall[
            pb_StreamWorldActionStatusRequest,
            pb_StreamWorldActionStatusResponse,
        ] = self._stub.StreamWorldActionStatus(
            request, metadata=self._metadata
        )

        _logger.debug("Streaming WorldAction status")
        streamer = WorldActionStatusResultStreamer()

        try:
            async for response in response_stream:
                for result in streamer.process(response):
                    yield result
        except grpc.RpcError as e:
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

    async def _create_and_get_single_world_action(
        self, expected_type: _WorldResultValueType, payload: pb_WorldPayload
    ) -> _WorldResultValue:
        self._check_not_closed()
        world_id = await self._create_world_action((payload,))

        results = [
            result async for result in self._stream_world_results(world_id)
        ]
        if len(results) != 1:
            raise CommunicationError(
                "WorldAction has unexpected number of WorldPayloads. "
                f"expected=1, actual={len(results)}, {world_id=}, {results=}"
            )

        result = results[0]
        return check_and_get_world_result_type(
            expected_type, world_id, 0, result
        )

    async def _subscribe_world_subs(
        self, subscriptions: Collection[pb_WorldSubscription]
    ) -> AsyncGenerator[pb_WorldSubscriptionUpdate]:
        self._check_not_closed()

        if _logger.isEnabledFor(logging.INFO):
            _logger.info(
                "Subscribing to WorldSubscriptions: %s",
                [pb_WorldSubscription.Name(sub) for sub in subscriptions],
            )

        request = pb_SubscribeWorldSubscriptionUpdatesRequest(
            subscriptions=subscriptions
        )
        response_stream: grpc.aio.UnaryStreamCall[
            pb_SubscribeWorldSubscriptionUpdatesRequest,
            pb_SubscribeWorldSubscriptionUpdatesResponse,
        ] = self._stub.SubscribeWorldSubscriptionUpdates(
            request, metadata=self._metadata
        )

        try:
            async for response in response_stream:
                _logger.debug(
                    "Got WorldSubscriptionUpdate: %s", response.update
                )
                yield response.update
        except grpc.RpcError as e:
            raise CommunicationError(
                "Error while subscribed to WorldSubscriptionUpdates: "
                f"{request=}"
            ) from e
        finally:
            # Cancel the call when the generator is closed
            response_stream.cancel()

        raise RuntimeError("WorldSubscription loop ended unexpectedly")

    def batch(self, *, wait: bool = True) -> "AsyncBatch":
        """Creates a new batch of payloads

        See :class:`AsyncBatch` for details.
        """
        self._check_not_closed()
        return AsyncBatch(_client=self, _wait=wait)


@dataclasses.dataclass(frozen=True)
class _FutureCallback[T]:
    fn: Callable[["AsyncBatchFuture[T]"], object]
    context: contextvars.Context


class AsyncBatchFuture[T](Awaitable[T]):
    """Future that can be used to check the status or retrieve the
    result of a payload that was created by an :class:`AsyncBatch`.

    This class is based on :class:`asyncio.Future`, and works mostly the
    same way.

    This class is not thread-safe. It must only be accessed from the
    event loop.

    :param [T]: Type of the result
    """

    __slots__ = (
        "_batch_started",
        "_callbacks",
        "_future",
        "_payload",
        "_payload_index",
        "_result_type",
        "_retrieved_exception_callback",
    )

    def __init__(
        self,
        *,
        _result_type: _WorldResultValueType,
        _payload: pb_WorldPayload,
        _payload_index: int,
        _future: asyncio.Future[T],
        _retrieved_exception_callback: Callable[[], None],
    ) -> None:
        self._result_type = _result_type
        self._payload_index = _payload_index
        self._payload = _payload
        self._future = _future
        self._batch_started = False
        self._callbacks: list[_FutureCallback[T]] = []
        self._retrieved_exception_callback = _retrieved_exception_callback

    def _check_batch_started(self) -> None:
        if not self._batch_started:
            raise asyncio.InvalidStateError(
                "Payload results cannot be accessed until the action has been "
                "sent to the Minecraft server (the context manager has exited)"
            )

    def __await__(self) -> Generator[Any, None, T]:
        """Waits until the payload finishes, then returns the result

        :raises WorldActionFailedError: if this payload or a previous
            payload in the action fails
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises asyncio.InvalidStateError: if the action hasn't been
            sent to the server yet
        :raises asyncio.CancelledError: if the future is cancelled
        """
        self._check_batch_started()

        # This basically just delegates to `self._future.__await__`, but
        # if an exception is raised, we call `self.exception` before
        # throwing so that `_retrieved_exception_callback` is called
        try:
            result = yield from self._future.__await__()
        except BaseException:
            if self._future.done() and not self._future.cancelled():
                self.exception()
            raise

        return result

    def result(self) -> T:
        """Returns the result

        :raises WorldActionFailedError: if this payload or a previous
            payload in the action fails
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises asyncio.InvalidStateError: if the action hasn't been
            sent to the server or the payload hasn't finished yet
        :raises asyncio.CancelledError: if the future is cancelled
        """
        self._check_batch_started()
        # Retrieve the exception so `_retrieved_exception_callback` is
        # called if needed
        self.exception()
        return self._future.result()

    def done(self) -> bool:
        """Returns ``True`` if the future is *done*

        The future is *done* if the payload has completed successfully,
        the payload failed, or the future was cancelled.
        """
        return self._future.done()

    def cancelled(self) -> bool:
        """Returns ``True`` if the future was cancelled"""
        return self._future.cancelled()

    def _schedule_callbacks(self) -> None:
        for callback in self._callbacks:
            self._future.get_loop().call_soon(
                callback.fn, self, context=callback.context
            )

        # Clear the callbacks so we don't keep a reference to them
        # (allows them to be garbage-collected)
        self._callbacks.clear()

    # TODO: Test the callback context
    def add_done_callback(
        self,
        fn: Callable[["AsyncBatchFuture[T]"], object],
        *,
        context: contextvars.Context | None = None,
    ) -> None:
        """Schedules the callback so that it will be run on the event
        loop once this future is done

        The callback will be called with the given ``context``, or with
        the current context if ``None``.

        If this future is already done, the callback will be called
        soon.

        If the same callback is added multiple times, it will be called
        once for each time it was added.
        """
        # We can't just call `self._future.add_done_callback()` because
        # we need the callback to be called with our AsyncBatchFuture,
        # not the asyncio.Future. So we need to track the callbacks
        # ourselves
        if self.done():
            # Future already done; schedule it now
            self._future.get_loop().call_soon(fn, self, context=context)
        else:
            if context is None:
                context = contextvars.copy_context()
            callback = _FutureCallback(fn, context)
            self._callbacks.append(callback)

    def remove_done_callback(
        self, fn: Callable[["AsyncBatchFuture[T]"], object]
    ) -> int:
        """Removes a callback that was previously added with
        :meth:`add_done_callback`

        If the callback wasn't previously added, this will have no
        effect.

        :return: The number of callbacks that were removed. Usually this
            is 0 or 1, but it may be greater if the callback was added
            via :meth:`add_done_callback` multiple times
        """
        old_count = len(self._callbacks)
        self._callbacks = [c for c in self._callbacks if c.fn != fn]
        new_count = len(self._callbacks)
        return old_count - new_count

    def exception(self) -> BaseException | None:
        """Returns the exception if the payload failed, or ``None`` if
        it succeeded

        :raises asyncio.InvalidStateError: if the action hasn't been
            sent to the server or the payload hasn't finished yet
        :raises asyncio.CancelledError: if the future is cancelled
        """
        self._check_batch_started()
        exception = self._future.exception()
        if exception is not None:
            self._retrieved_exception_callback()
        return exception

    def _start_batch(self) -> None:
        self._batch_started = True

    def _set_result(self, result: T) -> None:
        self._future.set_result(result)
        self._schedule_callbacks()

    def _set_exception(self, exception: BaseException) -> None:
        self._future.set_exception(exception)
        self._schedule_callbacks()

    def _cancel(self, msg: str | None = None) -> None:
        self._future.cancel(msg)

        # Unlike `set_result()` and `set_exception()`, `cancel()` may be
        # called multiple times. It's safe to call this though because
        # we clear the callbacks list after the first time
        self._schedule_callbacks()

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(index={self._payload_index}, "
            f"future={self._future})"
        )


# TODO: Make sure we can't submit the batch after the AsyncClient is
#       closed (also for SyncBatch)
class AsyncBatch:
    """Class that's used to asynchronously run a batch of tasks on the
    Minecraft server

    This class shouldn't be created directly. Use
    :meth:`AsyncClient.batch`.

    This class is not thread-safe. It must only be accessed from the
    event loop.

    The batch works by creating a single *action* and sending it to the
    Minecraft server to be processed. Each method in this class adds a
    *payload* (which represents a single task) to the action.

    This class provides the same basic functionality as the methods that
    are available directly in :class:`AsyncClient`, but using a batch
    causes the payloads to be submitted to the computer in a single
    network call (as a single action). This ensures that the timing
    between the payloads is consistent, which makes time-sensitive
    tasks such as interacting with redstone more reliable.

    This class must be used as a context manager. For example::

        async with client.batch(wait=True) as batch:
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

        async with client.batch(wait=False) as batch:
            future1 = batch.sensor.get_location()
            future2 = batch.sleep(20)
            future3 = batch.redstone.get_inputs()

        for future in (future1, future2, future3):
            result = await future
            print("Got result:", result)

    If any of the payloads fail, the exception will be raised by the
    future. Be sure to await the futures when ``wait`` is ``False``.
    """

    __slots__ = (
        "_client",
        "_futures",
        "_redstone",
        "_retrieved_exception",
        "_sensor",
        "_sound",
        "_state",
        "_wait",
    )

    _TASK_NAMER: Final = ThreadNamer("batch", thread_safe=False)

    def __init__(self, *, _client: AsyncClient, _wait: bool) -> None:
        self._client = _client
        self._wait = _wait
        self._futures: list[AsyncBatchFuture[Any]] = []
        self._state = ContextState.NEW
        self._retrieved_exception = False

        self._redstone = AsyncBatchRedstoneService(_batch=self)
        self._sensor = AsyncBatchSensorService(_batch=self)
        self._sound = AsyncBatchSoundService(_batch=self)

    @property
    def redstone(self) -> AsyncBatchRedstoneService:
        """Returns a service that can be used to interact with
        redstone"""
        return self._redstone

    @property
    def sensor(self) -> AsyncBatchSensorService:
        """Returns a service that can be used to get misc info"""
        return self._sensor

    @property
    def sound(self) -> AsyncBatchSoundService:
        """Returns a service that can be used to play sounds"""
        return self._sound

    def _check_entered(self) -> None:
        if self._state is not ContextState.ENTERED:
            raise RuntimeError(
                "AsyncBatch not entered. It must be used as a context manager"
            )

    async def __aenter__(self) -> Self:
        if self._state is not ContextState.NEW:
            raise RuntimeError("AsyncBatch already entered")
        self._state = ContextState.ENTERED
        return self

    async def __aexit__(
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
        the :class:`AsyncBatchFuture` objects.

        :raises WorldActionFailedError: if a payload fails (only when
            ``wait`` is ``True``)
        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
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
            await self._run_batch()
        else:
            task = asyncio.create_task(
                self._run_batch(), name=AsyncBatch._TASK_NAMER.next()
            )
            self._client._batch_tasks.add(task)
            task.add_done_callback(self._client._batch_tasks.discard)

        return False

    async def _run_batch(self) -> None:
        _logger.debug("Running batch")
        try:
            await self._run_batch_inner()
        except asyncio.CancelledError:
            self._cancel_remaining_futures()
            raise
        except BaseException as e:
            self._propagate_exception(e)

    async def _run_batch_inner(self) -> None:
        payloads = [future._payload for future in self._futures]
        assert len(payloads) > 0

        world_id = await self._client._create_world_action(payloads)
        payload_index = 0

        async for result in self._client._stream_world_results(world_id):
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
        assert not isinstance(exception, asyncio.CancelledError)
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
                # Retrieve the exception immediately so the user isn't
                # warned about never-retrieved exceptions. See
                # `_retrieve_all_future_exceptions`
                future.exception()

        if self._wait:
            # Raise the exception immediately so it's thrown in the
            # context manager
            raise
        elif not propagated_exception:
            # TODO: Propagate the exception to the loop's exception
            #       handler
            #
            #       Ref: https://docs.python.org/3/library/asyncio-eventloop.html#error-handling-api

            # This shouldn't happen. Probably a bug
            _logger.error(
                "Batch failed, but all WorldPayloads have already completed. "
                "Unable to propagate the exception",
                exc_info=exception,
            )

    def _retrieve_all_future_exceptions(self) -> None:
        """When the exception of a single future is retrieved,
        automatically retrieve the exceptions of the other failed
        futures as well

        This prevents asyncio from logging warnings about
        never-retrieved futures except when it's actually needed. Since
        the same exception is propagated to multiple futures, we don't
        want to make the user retrieve the same exception multiple
        times.

        When ``wait`` is ``False``, the user only needs to await the
        first failed future.

        When ``wait`` is ``True``, the exception will be thrown by the
        context manager, so the user doesn't need to await any of the
        futures. In this case, the exceptions will be retrieved by
        ``_propagate_exception``.
        """
        if self._retrieved_exception:
            return

        _logger.debug("Batch exception retrieved by user")
        self._retrieved_exception = True
        for future in self._futures:
            if future.done():
                future.exception()

    def _create_future(
        self, result_type: _WorldResultValueType, payload: pb_WorldPayload
    ) -> AsyncBatchFuture[Any]:
        self._check_entered()

        future = AsyncBatchFuture(
            _result_type=result_type,
            _payload_index=len(self._futures),
            _payload=payload,
            _future=asyncio.get_running_loop().create_future(),
            _retrieved_exception_callback=self._retrieve_all_future_exceptions,
        )
        self._futures.append(future)
        return future

    def sleep(self, ticks: int) -> AsyncBatchFuture[None]:
        """Waits for the specified number of game ticks before moving on
        to the next payload

        Note that this uses *game* ticks, not *redstone* ticks. There
        are 20 game ticks in a second, and 2 game ticks equals 1
        redstone tick.
        """
        payload = pb_WorldPayload(sleep=pb_Sleep(ticks=ticks))
        return self._create_future(_WorldResultValueType.NO_VALUE, payload)

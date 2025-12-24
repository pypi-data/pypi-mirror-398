__all__ = (
    "AsyncBatchRedstoneService",
    "AsyncRedstoneService",
    "SyncBatchRedstoneService",
    "SyncRedstoneService",
)

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING

from ._proto.clustercomputers.world.actions.get_redstone_inputs_pb2 import (
    GetRedstoneInputs as pb_GetRedstoneInputs,
)
from ._proto.clustercomputers.world.actions.get_redstone_outputs_pb2 import (
    GetRedstoneOutputs as pb_GetRedstoneOutputs,
)
from ._proto.clustercomputers.world.actions.set_all_redstone_outputs_pb2 import (
    SetAllRedstoneOutputs as pb_SetAllRedstoneOutputs,
)
from ._proto.clustercomputers.world.actions.set_redstone_output_pb2 import (
    SetRedstoneOutput as pb_SetRedstoneOutput,
)
from ._proto.clustercomputers.world.actions.world_payload_pb2 import (
    WorldPayload as pb_WorldPayload,
)
from ._proto.clustercomputers.world.subscriptions.world_subscription_pb2 import (
    WorldSubscription as pb_WorldSubscription,
)
from ._util import check_world_sub_type
from .world import (
    BlockSide,
    RedstoneSides,
    SideRedstoneSignal,
    _WorldResultValueType,
)

if TYPE_CHECKING:
    from .aclient import AsyncBatch, AsyncBatchFuture, AsyncClient
    from .sclient import SyncBatch, SyncBatchFuture, SyncClient


class SyncRedstoneService:
    """Sync service that can be used to interact with redstone

    This class should not be created directly. Use
    :attr:`SyncClient.redstone`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "SyncClient") -> None:
        self._client = _client

    def get_inputs(self) -> RedstoneSides:
        """Gets the redstone inputs for all sides

        This returns the redstone signals that are currently being
        *received* by the computer. To get the signals that are being
        *emitted* by the computer, use :meth:`get_outputs`.

        To monitor changes to the redstone inputs in real time, use
        :meth:`subscribe_updates`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(get_redstone_inputs=pb_GetRedstoneInputs())
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )
        assert isinstance(result, RedstoneSides)
        return result

    def get_outputs(self) -> RedstoneSides:
        """Gets the redstone outputs for all sides

        This returns the redstone signals that are currently being
        *emitted* by the computer. To get the signals that are being
        *received* by the computer, use :meth:`get_inputs`.

        The redstone outputs can be set via :meth:`set_all_outputs` or
        :meth:`set_output`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(get_redstone_outputs=pb_GetRedstoneOutputs())
        result = self._client._create_and_get_single_world_action(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )
        assert isinstance(result, RedstoneSides)
        return result

    def set_all_outputs(self, sides: RedstoneSides) -> None:
        """Sets the redstone outputs of all sides

        To set the output of a single side, use :meth:`set_output`.

        To get the current outputs, use :meth:`get_outputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        payload = pb_WorldPayload(
            set_all_redstone_outputs=pb_SetAllRedstoneOutputs(
                sides=sides._to_proto()
            )
        )
        self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )

    def set_output(self, side: BlockSide, strength: int) -> None:
        """Sets the redstone output of a single side

        To set the output of all sides at once, use
        :meth:`set_all_outputs`.

        To get the current outputs, use :meth:`get_outputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        signal = SideRedstoneSignal(side, strength)
        payload = pb_WorldPayload(
            set_redstone_output=pb_SetRedstoneOutput(signal=signal._to_proto())
        )
        self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )

    def subscribe_updates(self) -> Generator[SideRedstoneSignal]:
        """Yields real-time updates whenever a redstone input changes

        This method will run forever until the generator or client is
        closed.

        To just get the current inputs without real-time updates, use
        :meth:`get_inputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        :raises CancelledError: if this client is closed
        """
        subs = (pb_WorldSubscription.WORLD_SUBSCRIPTION_REDSTONE_UPDATE,)
        for update in self._client._subscribe_world_subs(subs):
            check_world_sub_type("redstone_update", update)
            yield SideRedstoneSignal._from_proto(update.redstone_update.input)


class SyncBatchRedstoneService:
    """Sync batch service that can be used to interact with redstone

    This class should not be created directly. Use
    :attr:`SyncBatch.redstone`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "SyncBatch") -> None:
        self._batch = _batch

    def get_inputs(self) -> "SyncBatchFuture[RedstoneSides]":
        """Gets the redstone inputs for all sides

        This returns the redstone signals that are currently being
        *received* by the computer. To get the signals that are being
        *emitted* by the computer, use :meth:`get_outputs`.

        To monitor changes to the redstone inputs in real time, use
        :meth:`SyncRedstoneService.subscribe_updates`.
        """
        payload = pb_WorldPayload(get_redstone_inputs=pb_GetRedstoneInputs())
        return self._batch._create_future(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )

    def get_outputs(self) -> "SyncBatchFuture[RedstoneSides]":
        """Gets the redstone outputs for all sides

        This returns the redstone signals that are currently being
        *emitted* by the computer. To get the signals that are being
        *received* by the computer, use :meth:`get_inputs`.

        The redstone outputs can be set via :meth:`set_all_outputs` or
        :meth:`set_output`.
        """
        payload = pb_WorldPayload(get_redstone_outputs=pb_GetRedstoneOutputs())
        return self._batch._create_future(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )

    def set_all_outputs(self, sides: RedstoneSides) -> "SyncBatchFuture[None]":
        """Sets the redstone outputs of all sides

        To set the output of a single side, use :meth:`set_output`.

        To get the current outputs, use :meth:`get_outputs`.
        """
        payload = pb_WorldPayload(
            set_all_redstone_outputs=pb_SetAllRedstoneOutputs(
                sides=sides._to_proto()
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )

    def set_output(
        self, side: BlockSide, strength: int
    ) -> "SyncBatchFuture[None]":
        """Sets the redstone output of a single side

        To set the output of all sides at once, use
        :meth:`set_all_outputs`.

        To get the current outputs, use :meth:`get_outputs`.
        """
        signal = SideRedstoneSignal(side, strength)
        payload = pb_WorldPayload(
            set_redstone_output=pb_SetRedstoneOutput(signal=signal._to_proto())
        )
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )


class AsyncRedstoneService:
    """Async service that can be used to interact with redstone

    This class should not be created directly. Use
    :attr:`AsyncClient.redstone`.
    """

    __slots__ = ("_client",)

    def __init__(self, *, _client: "AsyncClient") -> None:
        self._client = _client

    async def get_inputs(self) -> RedstoneSides:
        """Gets the redstone inputs for all sides

        This returns the redstone signals that are currently being
        *received* by the computer. To get the signals that are being
        *emitted* by the computer, use :meth:`get_outputs`.

        To monitor changes to the redstone inputs in real time, use
        :meth:`subscribe_updates`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(get_redstone_inputs=pb_GetRedstoneInputs())
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )
        assert isinstance(result, RedstoneSides)
        return result

    async def get_outputs(self) -> RedstoneSides:
        """Gets the redstone outputs for all sides

        This returns the redstone signals that are currently being
        *emitted* by the computer. To get the signals that are being
        *received* by the computer, use :meth:`get_inputs`.

        The redstone outputs can be set via :meth:`set_all_outputs` or
        :meth:`set_output`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(get_redstone_outputs=pb_GetRedstoneOutputs())
        result = await self._client._create_and_get_single_world_action(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )
        assert isinstance(result, RedstoneSides)
        return result

    async def set_all_outputs(self, sides: RedstoneSides) -> None:
        """Sets the redstone outputs of all sides

        To set the output of a single side, use :meth:`set_output`.

        To get the current outputs, use :meth:`get_outputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        payload = pb_WorldPayload(
            set_all_redstone_outputs=pb_SetAllRedstoneOutputs(
                sides=sides._to_proto()
            )
        )
        await self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )

    async def set_output(self, side: BlockSide, strength: int) -> None:
        """Sets the redstone output of a single side

        To set the output of all sides at once, use
        :meth:`set_all_outputs`.

        To get the current outputs, use :meth:`get_outputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        signal = SideRedstoneSignal(side, strength)
        payload = pb_WorldPayload(
            set_redstone_output=pb_SetRedstoneOutput(signal=signal._to_proto())
        )
        await self._client._create_and_get_single_world_action(
            _WorldResultValueType.NO_VALUE, payload
        )

    async def subscribe_updates(
        self,
    ) -> AsyncGenerator[SideRedstoneSignal]:
        """Yields real-time updates whenever a redstone input changes

        This method will run forever until the generator is closed or
        the coroutine is cancelled.

        To just get the current inputs without real-time updates, use
        :meth:`get_inputs`.

        :raises CommunicationError: if a communication error occurs with
            the podinterface
        """
        subs = (pb_WorldSubscription.WORLD_SUBSCRIPTION_REDSTONE_UPDATE,)
        async for update in self._client._subscribe_world_subs(subs):
            check_world_sub_type("redstone_update", update)
            yield SideRedstoneSignal._from_proto(update.redstone_update.input)


class AsyncBatchRedstoneService:
    """Async batch service that can be used to interact with redstone

    This class should not be created directly. Use
    :attr:`AsyncBatch.redstone`.
    """

    __slots__ = ("_batch",)

    def __init__(self, *, _batch: "AsyncBatch") -> None:
        self._batch = _batch

    def get_inputs(self) -> "AsyncBatchFuture[RedstoneSides]":
        """Gets the redstone inputs for all sides

        This returns the redstone signals that are currently being
        *received* by the computer. To get the signals that are being
        *emitted* by the computer, use :meth:`get_outputs`.

        To monitor changes to the redstone inputs in real time, use
        :meth:`AsyncRedstoneService.subscribe_updates`.
        """
        payload = pb_WorldPayload(get_redstone_inputs=pb_GetRedstoneInputs())
        return self._batch._create_future(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )

    def get_outputs(self) -> "AsyncBatchFuture[RedstoneSides]":
        """Gets the redstone outputs for all sides

        This returns the redstone signals that are currently being
        *emitted* by the computer. To get the signals that are being
        *received* by the computer, use :meth:`get_inputs`.

        The redstone outputs can be set via :meth:`set_all_outputs` or
        :meth:`set_output`.
        """
        payload = pb_WorldPayload(get_redstone_outputs=pb_GetRedstoneOutputs())
        return self._batch._create_future(
            _WorldResultValueType.REDSTONE_SIDES, payload
        )

    def set_all_outputs(
        self, sides: RedstoneSides
    ) -> "AsyncBatchFuture[None]":
        """Sets the redstone outputs of all sides

        To set the output of a single side, use :meth:`set_output`.

        To get the current outputs, use :meth:`get_outputs`.
        """
        payload = pb_WorldPayload(
            set_all_redstone_outputs=pb_SetAllRedstoneOutputs(
                sides=sides._to_proto()
            )
        )
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )

    def set_output(
        self, side: BlockSide, strength: int
    ) -> "AsyncBatchFuture[None]":
        """Sets the redstone output of a single side

        To set the output of all sides at once, use
        :meth:`set_all_outputs`.

        To get the current outputs, use :meth:`get_outputs`.
        """
        signal = SideRedstoneSignal(side, strength)
        payload = pb_WorldPayload(
            set_redstone_output=pb_SetRedstoneOutput(signal=signal._to_proto())
        )
        return self._batch._create_future(
            _WorldResultValueType.NO_VALUE, payload
        )

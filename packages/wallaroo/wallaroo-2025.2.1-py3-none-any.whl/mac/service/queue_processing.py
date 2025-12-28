"""This module features the producer/consumer pattern to process and consume
inference requests from separate threads using thread-safe queues. This is
required since `flight.FlightServerBase` is multi-threaded, i.e. it serves
multiple requests in separate threads, therefore we need to ensure thread-safe
access to the inference data when calling the `AsyncPythonStep`."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Generic, TypeVar

from mac.types import AsyncPythonStep, InferenceData

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OneShotChannel(Generic[T]):
    """This class features a one-shot channel for sending a single response.

    Attributes:
        - event: The event to signal completion.
        - data: The response data propagated through the channel.
        - error: The error propagated through the channel if any.
    """

    def __init__(self):
        self._event: asyncio.Event = asyncio.Event()
        self._data: T | None = None
        self._error: Exception | None = None

    async def send(self, data: T) -> None:
        """Send the response data and signal completion.

        :param data: The response data.

        :raises RuntimeError: If the channel is already used.
        """
        assert not self._event.is_set(), "Channel already used."
        self._data = data
        self._event.set()

    async def send_error(self, error: Exception) -> None:
        """Send an error and signal completion.

        :param error: The error.

        :raises RuntimeError: If the channel is already used.
        """
        assert not self._event.is_set(), "Channel already used."
        self._error = error
        self._event.set()

    async def receive(self, timeout: float | None = None) -> T:
        """Wait for and return the response value.

        :param timeout: The timeout.

        :return: The response value.
        """
        try:
            await asyncio.wait_for(self._event.wait(), timeout)
            if self._error:
                raise self._error
            assert self._data is not None, "Channel has no data to return."
            return self._data
        finally:
            self._clear_channel()

    def _clear_channel(self) -> None:
        """Clear the channel by resetting data and error."""
        self._data = None
        self._error = None


@dataclass
class QueueData:
    """This dataclass stores a request id and its inference data
    to be stored and consumed from a queue, together with a one-shot response
    channel to send the result associated with the request."""

    request_id: str
    inference_data: InferenceData
    response_channel: OneShotChannel[InferenceData]

    def __repr__(self) -> str:
        return (
            f"QueueData(request_id='{self.request_id}', "
            f"inference_data={self.inference_data}, "
            f"response_channel=OneShotChannel<InferenceData>)"
        )


class PythonStepConsumer:
    """This class is responsible for processing `InferenceData` from `QueueData`
    instances and sending the result through their one-shot response channels.

    Attributes:
        - python_step: The `PythonStep` to process the inference data.
        - queue: The queue to get the inference data from.
        - task: The task running the consumer loop.
    """

    def __init__(
        self,
        python_step: AsyncPythonStep,
        queue: asyncio.Queue,
    ):
        self._python_step = python_step
        self._queue = queue
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start the consumer processing loop."""
        assert self._task is None, "Queue processor is already running."
        self._task = asyncio.create_task(self._run())

    def stop(self) -> None:
        """Stop the consumer processing loop."""
        assert self.is_running, "Consumer processing loop is not running."
        assert self._queue.empty(), "Cannot stop consumer while queue is not empty."
        self._task.cancel()  # type: ignore[union-attr]

    async def _run(self) -> None:
        """Processing loop that awaits for input in the queue, parses them to
        the python step and sends the result through a one-shot response
        channel.
        """
        logger.info("Starting consumer processing loop...")

        while True:
            try:
                logger.debug("Waiting for `QueueData`...")
                queue_data: QueueData = await self._queue.get()
                logger.debug("Got `QueueData` from queue.")
                asyncio.create_task(self._process_step(queue_data))
            except Exception as e:
                logger.exception("Error in consumer processing loop: %s", str(e))

    async def _process_step(self, queue_data: QueueData) -> None:
        try:
            result: InferenceData = await self._python_step(queue_data.inference_data)
            logger.debug("Sending result through one-shot response channel...")
            await queue_data.response_channel.send(result)
            logger.debug("Result sent through one-shot response channel.")
        except Exception as e:
            logger.exception(
                "Error processing step for `request_id` `%s`: %s",
                queue_data.request_id,
                str(e),
            )
            await queue_data.response_channel.send_error(e)


class PythonStepProducer:
    """This class is responsible for producing `QueueData` instances for an
    `AsyncPythonStep` and assigning them to a queue.

    Attributes:
        - queue: The queue to put the `QueueData` in.
    """

    def __init__(self, queue: asyncio.Queue):
        self._queue = queue

    async def submit(
        self,
        request_id: str,
        inference_data: InferenceData,
    ) -> OneShotChannel[InferenceData]:
        """Submit request to the processing queue. Returns a one-shot response
        channel to receive the result.

        :param request_id: The request id.
        :param inference_data: The inference data.

        :return: A response channel to receive the result.
        """
        logger.debug(
            "Submitting `InferenceData` to queue with request id `%s`...",
            request_id,
        )

        response_channel = OneShotChannel[InferenceData]()
        await self._queue.put(
            QueueData(
                request_id=request_id,
                inference_data=inference_data,
                response_channel=response_channel,
            )
        )

        logger.debug("Submitted request with id `%s` to the queue.", request_id)

        return response_channel

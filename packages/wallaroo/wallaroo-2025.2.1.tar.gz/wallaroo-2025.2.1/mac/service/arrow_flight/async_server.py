"""This module features the `AsyncArrowFlightServer` class that implements a
`IArrowFlightServer` to serve a `PythonStep` asynchronously."""

import asyncio
import logging
import threading
import uuid
from typing import List

import pyarrow as pa
from pydata_util.decorators import measure_time
from pydata_util.pyarrow.converter_factory import (
    ArrowToNDArrayFactory,
    NDArrayToArrowFactory,
)

from mac.config.service import ServerConfig
from mac.exceptions import (
    PythonStepError,
)
from mac.service.arrow_flight.base_server import IArrowFlightServer
from mac.service.queue_processing import (
    OneShotChannel,
    PythonStepConsumer,
    PythonStepProducer,
)
from mac.types import (
    AsyncPythonStep,
    InferenceData,
)

logger = logging.getLogger(__name__)


class AsyncArrowFlightServer(IArrowFlightServer):
    """This class implements the asynchronous Arrow Flight server,
    that can be used to serve an `AsyncPythonStep` via the Arrow Flight RPC protocol.

    Attributes:
        - server_config: A `ServerConfig` object.
        - output_schema: A `pyarrow.Schema` object representing the output schema.
        - arrow_to_ndarray_factory: An `ArrowToNDArrayFactory` object.
        - ndarray_to_arrow_factory: An `NDArrayToArrowFactory` object.
        - location: A string representing the location of the server.
        - python_step: A `PythonStep` callable to serve.
        - max_queue_depth: An integer representing the maximum queue depth.
        - request_timeout: A float representing the request timeout.
        - event_loop: An `asyncio.AbstractEventLoop` object.
        - producer: A `PythonStepProducer` object.
        - consumer: A `PythonStepConsumer` object.
    """

    def __init__(
        self,
        python_step: AsyncPythonStep,
        server_config: ServerConfig,
        output_schema: pa.Schema,
        arrow_to_ndarray_factory: ArrowToNDArrayFactory = ArrowToNDArrayFactory(),
        ndarray_to_arrow_factory: NDArrayToArrowFactory = NDArrayToArrowFactory(),
        max_queue_depth: int = 128,
        request_timeout: None | float = None,
    ):
        super().__init__(
            server_config=server_config,
            output_schema=output_schema,
            arrow_to_ndarray_factory=arrow_to_ndarray_factory,
            ndarray_to_arrow_factory=ndarray_to_arrow_factory,
        )

        self._python_step = python_step
        self._max_queue_depth = max_queue_depth
        self._request_timeout = request_timeout
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._producer: PythonStepProducer | None = None
        self._consumer: PythonStepConsumer | None = None

        self._start_event_loop()
        self._start_queue_processing()

    def _start_event_loop(self):
        logger.info("Starting event loop in a separate thread...")
        self._event_loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        loop_thread.start()
        logger.info("Event loop started.")

    def _run_event_loop(self):
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_forever()

    def _start_queue_processing(self):
        """Spawn the async queue and run consumer in the background loop."""
        logger.info("Starting queue processing in the event loop...")
        queue = asyncio.run_coroutine_threadsafe(
            self._create_queue(), self._event_loop
        ).result()

        self._consumer = PythonStepConsumer(self._python_step, queue)
        self._producer = PythonStepProducer(queue)

        asyncio.run_coroutine_threadsafe(self._consumer.start(), self._event_loop)
        logger.info("Queue processing started.")

    async def _create_queue(self):
        return asyncio.Queue(maxsize=self._max_queue_depth)

    @measure_time
    def _run_inference_for_batch(self, batch: pa.RecordBatch) -> List[pa.RecordBatch]:
        logger.debug("Converting `pa.RecordBatch` to `InferenceData`...")
        inference_data = self._convert_record_batch_to_inference_data(batch)

        assert self._event_loop is not None and self._event_loop.is_running(), (
            "Event loop not started or not running."
        )

        logger.debug("Parsing `InferenceData` to `PythonStep`...")
        inference_data = asyncio.run_coroutine_threadsafe(
            self._run_python_step(inference_data), self._event_loop
        ).result()

        logger.debug("Converting `InferenceData` to `pa.RecordBatch`...")
        return self._convert_inference_data_to_record_batches(inference_data)

    @measure_time
    async def _run_python_step(self, inference_data: InferenceData) -> InferenceData:
        try:
            assert self._consumer is not None and self._consumer.is_running, (
                "Consumer not assigned or processing loop not running."
            )
            assert self._producer is not None, "Producer not assigned to server."

            request_id = uuid.uuid4().hex

            response_channel: OneShotChannel[
                InferenceData
            ] = await self._producer.submit(
                request_id=request_id,
                inference_data=inference_data,
            )

            logger.debug("Awaiting result for request id `%s`...", request_id)
            result = await response_channel.receive(timeout=self._request_timeout)
            logger.debug("Result received for request id `%s`.", request_id)
        except Exception as exc:
            message = "`AsyncPythonStep` call failed."
            logger.exception(message)
            raise PythonStepError(message) from exc
        return result

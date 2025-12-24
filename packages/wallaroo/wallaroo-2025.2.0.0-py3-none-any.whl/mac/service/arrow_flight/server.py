"""This module features the `ArrowFlightServer` class that implements a
`IArrowFlightServer` to serve a `PythonStep` synchronously."""

import logging
import threading
from contextlib import contextmanager
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
from mac.types import (
    InferenceData,
    PythonStep,
)

logger = logging.getLogger(__name__)


class ArrowFlightServer(IArrowFlightServer):
    """This class implements the (default) synchronous Arrow Flight server,
    that can be used to serve a `PythonStep` via the Arrow Flight RPC protocol.

    Attributes:
        - server_config: A `ServerConfig` object.
        - output_schema: A `pyarrow.Schema` object representing the output schema.
        - use_lock: A boolean indicating whether to use a lock to synchronize access to
            `PythonStep`.
        - arrow_to_ndarray_factory: An `ArrowToNDArrayFactory` object.
        - ndarray_to_arrow_factory: An `NDArrayToArrowFactory` object.
        - location: A string representing the location of the server.
        - python_step: A `PythonStep` callable to serve.
        - lock: A `threading.Lock` object.
    """

    def __init__(
        self,
        python_step: PythonStep,
        server_config: ServerConfig,
        output_schema: pa.Schema,
        use_lock: bool = True,
        arrow_to_ndarray_factory: ArrowToNDArrayFactory = ArrowToNDArrayFactory(),
        ndarray_to_arrow_factory: NDArrayToArrowFactory = NDArrayToArrowFactory(),
    ):
        super().__init__(
            server_config=server_config,
            output_schema=output_schema,
            arrow_to_ndarray_factory=arrow_to_ndarray_factory,
            ndarray_to_arrow_factory=ndarray_to_arrow_factory,
        )

        self._python_step = python_step
        self._lock: threading.Lock | None = (
            threading.Lock() if use_lock is True else None
        )

    @contextmanager
    def _acquire_lock_if_set(self):
        if self._lock:
            logger.debug("Acquiring lock...")
            self._lock.acquire()
        try:
            yield
        finally:
            if self._lock:
                logger.debug("Releasing lock...")
                self._lock.release()

    @measure_time
    def _run_inference_for_batch(self, batch: pa.RecordBatch) -> List[pa.RecordBatch]:
        logger.debug("Converting `pa.RecordBatch` to `InferenceData`...")
        inference_data = self._convert_record_batch_to_inference_data(batch)

        logger.debug("Parsing `InferenceData` to `PythonStep`...")
        inference_data = self._run_python_step(inference_data)

        logger.debug("Converting `InferenceData` to `pa.RecordBatch`...")
        return self._convert_inference_data_to_record_batches(inference_data)

    @measure_time
    def _run_python_step(self, inference_data: InferenceData) -> InferenceData:
        with self._acquire_lock_if_set():
            try:
                return self._python_step(inference_data)
            except Exception as exc:
                message = "`PythonStep` call failed."
                logger.exception(message)
                raise PythonStepError(message) from exc

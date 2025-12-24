"""This module features the `IArrowFlightServer` interface, that
implements a `flight.FlightServerBase` which serves a `PythonStep`."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Generator, List, Optional, Tuple

import numpy.typing as npt
import pyarrow as pa
import pyarrow.flight as flight
from pydata_util.decorators import log_error, measure_time
from pydata_util.pyarrow.converter_factory import (
    ArrowToNDArrayFactory,
    NDArrayToArrowFactory,
)
from pydata_util.pyarrow.data_inspectors import get_io_arrow_dtype_from_pa_dtype
from pydata_util.types import IOArrowDType

from mac.config.service import ServerConfig
from mac.exceptions import (
    ArrowΤοΝDArrayConversionError,
    FlightSchemaNotImplementedError,
    InferenceDataValidationError,
    InferencePreprocessingError,
    NDArrayToArrowConversionError,
    PythonStepError,
)
from mac.types import (
    InferenceData,
)

logger = logging.getLogger(__name__)


class IArrowFlightServer(ABC, flight.FlightServerBase):
    """This class implements the Arrow Flight server interface, that can be used to
    serve a `PythonStep` via the Arrow Flight RPC protocol.

    Attributes:
        - server_config: A `ServerConfig` object.
        - output_schema: A `pyarrow.Schema` object representing the output schema.
        - arrow_to_ndarray_factory: An `ArrowToNDArrayFactory` object.
        - ndarray_to_arrow_factory: An `NDArrayToArrowFactory` object.
        - location: A string representing the location of the server.
    """

    def __init__(
        self,
        server_config: ServerConfig,
        output_schema: pa.Schema,
        arrow_to_ndarray_factory: ArrowToNDArrayFactory = ArrowToNDArrayFactory(),
        ndarray_to_arrow_factory: NDArrayToArrowFactory = NDArrayToArrowFactory(),
    ):
        self._server_config = server_config
        self._output_schema = output_schema
        self._arrow_to_ndarray_factory = arrow_to_ndarray_factory
        self._ndarray_to_arrow_factory = ndarray_to_arrow_factory

        super().__init__(location=self.location)

    @property
    def location(self):
        """This property returns the location of the server."""
        return f"grpc://{self._server_config.host}:{self._server_config.port}"

    def do_action(
        self, context: flight.ServerCallContext, action: flight.Action
    ) -> Generator[flight.Result, None, None]:
        """This method implements the `do_action` method of the FlightServerBase,
        that provides a health check endpoint for the server.

        :param context: A ServerCallContext object.
        :param action: A FlightAction object.

        :return: A Generator of FlightResult objects.

        :raises KeyError: If the action type is not `ping`.
        """
        if action.type == "ping":
            yield flight.Result(pa.py_buffer(b"\n"))
        else:
            raise KeyError("Unknown action `%s`.", action.type)

    def do_exchange(
        self,
        context: flight.ServerCallContext,
        descriptor: flight.FlightDescriptor,
        reader: flight.FlightStreamReader,
        writer: flight.FlightStreamWriter,
    ) -> None:
        """This method implements the `do_exchange` method of the FlightServerBase
        class.

        :param context: A ServerCallContext object.
        :param descriptor: A FlightDescriptor object.
        :param reader: A FlightStreamReader object.
        :param writer: A FlightStreamWriter object.
        """
        is_first_batch = True
        while True:
            logger.info("Processing data...")
            (
                writer,
                reader,
                is_first_batch,
            ) = self._run_inference_and_write_to_stream(writer, reader, is_first_batch)
            logger.info("Output data ready to be consumed.")

    def get_schema(
        self, context: flight.ServerCallContext, descriptor: flight.FlightDescriptor
    ):
        """This method implements the `get_schema` method of the FlightServerBase
        class.

        :param context: A ServerCallContext object.
        :param descriptor: A FlightDescriptor object.

        :raises: A SchemaNotImplementedError.
        """
        message = (
            "`get_schema` RPC is not implemented, "
            "since `mac` has no information about the input schema."
        )
        logger.error(message)
        raise FlightSchemaNotImplementedError(message)

    @abstractmethod
    def _run_inference_for_batch(self, batch: pa.RecordBatch) -> List[pa.RecordBatch]:
        """This method implements the logic to run inference on a batch of data."""

    def _run_inference_and_write_to_stream(
        self,
        writer: flight.FlightStreamWriter,
        reader: flight.FlightStreamReader,
        is_first_batch: bool,
    ) -> Tuple[flight.FlightStreamWriter, flight.FlightStreamReader, bool]:
        logger.debug("Starting batch processing...")
        for batch in reader.read_chunk():
            if batch is None:
                break
            writer, is_first_batch = self._process_batch(  # type: ignore[no-redef]
                batch, writer, is_first_batch
            )
        logger.debug("Batch processing finished.")

        writer.close()

        return (writer, reader, is_first_batch)

    def _process_batch(
        self,
        batch: pa.RecordBatch,
        writer: flight.MetadataRecordBatchWriter,
        is_first_batch: bool,
    ) -> Tuple[flight.FlightStreamWriter, bool]:
        try:
            result = self._run_inference_for_batch(batch)
        except Exception as exc:
            message = "Failed to run inference on record batch."
            details = []
            cause: Optional[BaseException] = exc

            while cause is not None:
                details.append(str(cause))
                cause = cause.__cause__

            cause = exc.__cause__ if isinstance(exc, PythonStepError) else exc

            code = IArrowFlightServer._determine_status_code(cause)
            error = {
                "code": code,
                "message": message,
                "details": details,
            }

            extra_info = json.dumps(error).encode()
            raise flight.FlightServerError(
                message=message, extra_info=extra_info
            ) from exc

        return self._write_result(writer, result, is_first_batch)  # type: ignore

    @staticmethod
    def _determine_status_code(exc: Optional[BaseException]) -> int:
        # TODO which exceptions are 400 Bad Request?
        return (
            400
            if isinstance(
                exc,
                (
                    ArrowΤοΝDArrayConversionError,
                    InferenceDataValidationError,
                    InferencePreprocessingError,
                ),
            )
            else 500
        )

    @measure_time
    @log_error(
        ArrowΤοΝDArrayConversionError,
        "Failed to convert `pa.RecordBatch` to `InferenceData`.",
    )
    def _convert_record_batch_to_inference_data(
        self,
        batch: pa.RecordBatch,
    ) -> InferenceData:
        inference_data: InferenceData = {}

        for column, column_name in zip(batch, batch.schema.names):
            try:
                inference_data[column_name] = self._convert_arrow_to_ndarray(
                    column, column_name
                )
            except Exception as exc:
                logger.exception(
                    "Failed to convert input `pa.Array` `%s` to `npt.NDArray`.",
                    column_name,
                )
                raise exc

        return inference_data

    def _convert_arrow_to_ndarray(
        self,
        array: pa.Array,
        name: str,
    ) -> npt.NDArray:
        io_arrow_dtype: IOArrowDType = get_io_arrow_dtype_from_pa_dtype(
            pa_dtype=array.type
        )
        logger.debug(
            "Converting `pa.Array` `%s` of type `%s` to `npt.NDArray`...",
            name,
            io_arrow_dtype,
        )
        return self._arrow_to_ndarray_factory.create(io_arrow_dtype, array=array)

    @measure_time
    @log_error(
        NDArrayToArrowConversionError,
        "Failed to convert `InferenceData` to `pa.RecordBatch`.",
    )
    def _convert_inference_data_to_record_batches(
        self,
        inference_data: InferenceData,
    ) -> List[pa.RecordBatch]:
        return pa.Table.from_arrays(
            [
                self._convert_ndarray_to_arrow(
                    key, data, self._output_schema.field(key).type
                )
                for key, data in inference_data.items()
            ],
            schema=pa.schema(
                [
                    (key, self._output_schema.field(key).type)
                    for key in inference_data.keys()
                ]
            ),
        ).to_batches()

    def _convert_ndarray_to_arrow(
        self, key: str, data: npt.NDArray, pa_dtype: pa.DataType
    ) -> pa.Array:
        io_arrow_dtype: IOArrowDType = get_io_arrow_dtype_from_pa_dtype(
            pa_dtype=pa_dtype
        )
        converter_kwargs = self._get_converter_kwargs(data, pa_dtype, io_arrow_dtype)

        logger.debug(
            "Converting `npt.NDArray` `%s` to `pa.Array` of type `%s`...",
            key,
            io_arrow_dtype,
        )

        try:
            return self._ndarray_to_arrow_factory.create(
                io_arrow_dtype, **converter_kwargs
            )
        except Exception as exc:
            logger.exception(
                "Failed to convert output `npt.NDArray` `%s` to `pa.Array`.", key
            )
            raise exc

    @staticmethod
    def _get_converter_kwargs(
        data: npt.NDArray, pa_dtype: pa.DataType, io_arrow_dtype: IOArrowDType
    ) -> dict:
        return (
            {
                "pa_dtype": pa_dtype,
                "data": data,
            }
            if io_arrow_dtype in (IOArrowDType.LIST, IOArrowDType.FIXED_SIZE_LIST)
            else {
                "data": data,
            }
        )

    def _write_result(
        self,
        writer: flight.FlightStreamWriter,
        result: List[pa.RecordBatch],
        is_first_batch: bool,
    ) -> Tuple[flight.FlightStreamWriter, bool]:
        if is_first_batch is True:
            is_first_batch = False
            logger.debug("Writing schema to stream...")
            writer.begin(result[0].schema)

        for batch in result:
            writer.write_batch(batch)

        return (writer, is_first_batch)

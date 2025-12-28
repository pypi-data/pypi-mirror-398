from typing import Optional


class DynamicBatchingConfig:
    """Model configuration for dynamic batching"""

    def __init__(
        self,
        max_batch_delay_ms: int = 10,
        batch_size_target: int = 4,
        batch_size_limit: Optional[int] = None,
    ):
        """
        Initialize the DynamicBatchingConfig object.

        Attributes:
            max_batch_delay_ms (int): Maximum amount of time we will wait before sending a batch to the model for inference
            batch_size_target (int):  Minimum size of a batch we will send to the model.
            batch_size_limit (int, optional): Maximum size of a batch that the model can process. Defaults to None.
        """
        self.max_batch_delay_ms = max_batch_delay_ms
        self.batch_size_target = batch_size_target
        self.batch_size_limit = batch_size_limit

    @property
    def max_batch_delay_ms(self):
        """Get the maximum batch delay in milliseconds."""
        return self._max_batch_delay_ms

    @max_batch_delay_ms.setter
    def max_batch_delay_ms(self, max_batch_delay_ms: int):
        """
        Set the maximum batch delay in milliseconds.

        :param max_batch_delay_ms: Maximum batch delay in milliseconds.

        :raises ValueError: If value is not an integer or is less than or equal to 0.
        """
        self._validate_input(max_batch_delay_ms, "max_batch_delay_ms")
        self._max_batch_delay_ms = max_batch_delay_ms

    @property
    def batch_size_target(self):
        """Get the target batch size."""
        return self._batch_size_target

    @batch_size_target.setter
    def batch_size_target(self, batch_size_target: int):
        """
        Set the target batch size.

        :param batch_size_target: Target batch size.

        :raises ValueError: If value is not an integer or is less than or equal to 0.
        """
        self._validate_input(batch_size_target, "batch_size_target")
        self._batch_size_target = batch_size_target

    @property
    def batch_size_limit(self):
        """Get the batch size limit."""
        return self._batch_size_limit

    @batch_size_limit.setter
    def batch_size_limit(self, batch_size_limit: int):
        """
        Set the batch size limit.

        :param batch_size_limit: Batch size limit.

        :raises ValueError: If value is not an integer or is less than or equal to 0.
        """
        if batch_size_limit is not None:
            self._validate_input(batch_size_limit, "batch_size_limit")
        self._batch_size_limit = batch_size_limit

    @staticmethod
    def _validate_input(param_value, param_name):
        """
        Validate the input value.

        :param param_value: Input value to validate.
        :param param_name: Name of the input value.

        :raises ValueError: If value is not an integer or is less than or equal to 0.
        """
        if not isinstance(param_value, int):
            raise ValueError(f"{param_name} must be an integer")
        if param_value is not None and param_value <= 0:
            raise ValueError(f"{param_name} must be a positive integer or None")

    def __repr__(self):
        """
        Return a string representation of the DynamicBatchingConfig object.

        :return: String representation of the DynamicBatchingConfig object.
        """
        return (
            f"DynamicBatchingConfig("
            f"max_batch_delay_ms={self.max_batch_delay_ms}, "
            f"batch_size_target={self.batch_size_target}, "
            f"batch_size_limit={self.batch_size_limit})"
        )

    def to_json(self):
        """
        Convert the DynamicBatchingConfig object to a JSON object.

        :return: JSON representation of the DynamicBatchingConfig object.
        """
        return {
            "max_batch_delay_ms": self.max_batch_delay_ms,
            "batch_size_target": self.batch_size_target,
            "batch_size_limit": self.batch_size_limit,
        }

    @classmethod
    def from_dict(cls, config_dict):
        """
        Create a DynamicBatchingConfig object from a dictionary.

        :param config_dict: Dictionary containing the configuration values.

        :return: DynamicBatchingConfig: DynamicBatchingConfig object created from the dictionary.
        """
        if config_dict is None:
            return None
        return cls(**config_dict)

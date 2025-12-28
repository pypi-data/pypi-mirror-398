from dataclasses import dataclass
from functools import wraps
from typing import Optional

import httpx


@dataclass
class APIErrorResponse:
    """
    Standardized structure for API error responses.

    Attributes:
        code: HTTP status code of the error
        status: Status message (e.g., "error", "failed")
        error: Detailed error message
        source: Source of the error (e.g., "engine", "sidekick")
        original_response: Original response object for fallback
    """

    code: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None
    source: Optional[str] = None
    original_response: Optional[httpx.Response] = None

    # TODO: we need to implement the same for mlops api client and httpx client.
    @classmethod
    def from_response(cls, response: httpx.Response) -> "APIErrorResponse":
        """
        Create an APIErrorResponse from a httpx.Response object.
        Handles two error response structures:
        - axum-util: { "msg": "...", "code": 400 }
        - fitzroy: { "code": 400, "status": "Error", "error": "...", "source": "engine" }
        Falls back gracefully if expected fields are missing.
        """

        error_data = response.json()
        has_fitzroy_structure = (
            "error" in error_data or "status" in error_data or "source" in error_data
        )

        if has_fitzroy_structure:
            return cls(
                code=error_data.get("code", response.status_code),
                status=error_data.get("status"),
                error=error_data.get("error") or response.text,
                source=error_data.get("source"),
                original_response=response,
            )
        else:
            return cls(
                code=error_data.get("code", response.status_code),
                status=None,
                error=error_data.get("msg") or response.text,
                source=None,
                original_response=response,
            )


class WallarooAPIError(Exception):
    """
    Base exception class for all Wallaroo API errors.

    Attributes:
        code: HTTP status code of the error
        status: Status message
        error: Detailed error message
        source: Source of the error
        response: Original APIErrorResponse object
    """

    def __init__(self, error_response: APIErrorResponse, prefix: str = ""):
        self.code = error_response.code
        self.status = error_response.status
        self.error = error_response.error
        self.source = error_response.source
        self.response = error_response
        self.prefix = prefix

        # Format a consistent error message
        message = self.__str__()
        super().__init__(message)

    def __str__(self) -> str:
        error_msg = (
            f"{self.prefix}: [{self.code}] {self.error}"
            if self.prefix
            else f"[{self.code}] {self.error}"
        )
        if self.source:
            status_part = f", status: {self.status}" if self.status else ""
            return f"{error_msg} (source: {self.source}{status_part})"
        else:
            # axum-util structure - no source/status
            return error_msg


def handle_errors(http_error_class=None):
    """
    Decorator to handle HTTP errors and convert them to appropriate custom errors.

    :param error_class: The specific error class to use for HTTP errors.
                       If None, uses WallarooAPIError.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response is not None:
                    error_cls = http_error_class or WallarooAPIError
                    if error_cls.__init__ is WallarooAPIError.__init__:
                        error_response = APIErrorResponse.from_response(e.response)
                        raise error_cls(error_response) from e
                    else:
                        raise error_cls(e.response) from e
                raise  # Re-raise if no response available
            except httpx.RequestError:
                raise httpx.RequestError(
                    "An error occurred while sending the request. Check network configuration, adjust timeout if necessary and retry."
                )
            except httpx.HTTPError:
                raise httpx.HTTPError(
                    "An error occurred while sending the request. Check network configuration, adjust timeout if necessary and Retry again."
                )

        return wrapper

    return decorator


# Custom error classes
class InferenceError(WallarooAPIError):
    """Raised when inference fails"""

    def __init__(self, response: httpx.Response):
        error_response = APIErrorResponse.from_response(response)
        super().__init__(error_response, prefix="Inference failed")


class InferenceTimeoutError(Exception):
    """Raised when inference fails because of connection or timeout errors."""

    def __init__(self, error):
        super().__init__("Inference failed: {}".format(error))


class ModelUploadError(WallarooAPIError):
    """Raised when a model file fails to upload."""

    def __init__(self, response: httpx.Response):
        error_response = APIErrorResponse.from_response(response)
        super().__init__(error_response, prefix="Model failed to upload")

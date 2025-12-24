import httpx
import pytest
from httpx import Response

from wallaroo.exceptions import (
    APIErrorResponse,
    InferenceError,
    InferenceTimeoutError,
    ModelUploadError,
    WallarooAPIError,
    handle_errors,
)


# Fixtures
@pytest.fixture
def mock_response(mocker):
    response = mocker.Mock(spec=Response)
    response.status_code = 400
    return response


@pytest.fixture
def json_error_response(mock_response):
    """Fitzroy error structure: code, status, error, source"""
    mock_response.json.return_value = {
        "code": 400,
        "status": "error",
        "error": "Bad Request",
        "source": "engine",
    }
    return mock_response


@pytest.fixture
def axum_error_response(mock_response):
    """axum-util error structure: code, msg"""
    mock_response.json.return_value = {
        "code": 400,
        "msg": "Bad Request",
    }
    return mock_response


# Test APIErrorResponse
@pytest.mark.parametrize(
    "response_data,expected",
    [
        # Fitzroy structure - full
        (
            {
                "code": 429,
                "status": "Error",
                "error": "no available capacity",
                "source": "engine",
            },
            {
                "code": 429,
                "status": "Error",
                "error": "no available capacity",
                "source": "engine",
            },
        ),
        # Fitzroy structure - partial
        (
            {"status": "error", "error": "Some error"},
            {
                "code": 400,
                "status": "error",
                "error": "Some error",
                "source": None,
            },
        ),
        # axum-util structure
        (
            {"code": 400, "msg": "Bad Request"},
            {
                "code": 400,
                "status": None,
                "error": "Bad Request",
                "source": None,
            },
        ),
        # Empty JSON - falls back to response.text
        (
            {},
            {
                "code": 400,
                "status": None,
                "error": "",
                "source": None,
            },
        ),
    ],
)
def test_api_error_response_from_response(mock_response, response_data, expected):
    mock_response.json.return_value = response_data
    # Set response.text for cases where error/msg fallback is used
    if "error" not in response_data and "msg" not in response_data:
        mock_response.text = expected.get("error", "")

    error_response = APIErrorResponse.from_response(mock_response)

    assert error_response.code == expected["code"]
    assert error_response.status == expected["status"]
    assert error_response.error == expected["error"]
    assert error_response.source == expected["source"]
    assert error_response.original_response == mock_response


def test_api_error_response_fallback_to_text(mock_response):
    """Test fallback to response.text when error/msg not in JSON"""
    mock_response.json.return_value = {}
    mock_response.text = "Plain text error message"
    error_response = APIErrorResponse.from_response(mock_response)

    assert error_response.error == "Plain text error message"


# Test WallarooAPIError
@pytest.mark.parametrize(
    "response_data,prefix,expected_str",
    [
        # Fitzroy - full structure with prefix
        (
            {
                "code": 400,
                "status": "error",
                "error": "Bad Request",
                "source": "engine",
            },
            "Test Error",
            "Test Error: [400] Bad Request (source: engine, status: error)",
        ),
        # Fitzroy - without status
        (
            {"code": 404, "error": "Not Found", "source": "engine"},
            "",
            "[404] Not Found (source: engine)",
        ),
        # axum-util - no prefix
        (
            {"code": 400, "msg": "Bad Request"},
            "",
            "[400] Bad Request",
        ),
        # axum-util - with prefix
        (
            {"code": 500, "msg": "Internal server error"},
            "Upload failed",
            "Upload failed: [500] Internal server error",
        ),
    ],
)
def test_wallaroo_api_error_str_format(
    mock_response, response_data, prefix, expected_str
):
    mock_response.json.return_value = response_data
    error_response = APIErrorResponse.from_response(mock_response)
    error = WallarooAPIError(error_response, prefix=prefix)

    assert str(error) == expected_str


# Test handle_errors decorator
def test_handle_errors_successful_execution():
    @handle_errors()
    def successful_function():
        return "success"

    assert successful_function() == "success"


def test_handle_errors_with_custom_error_class(json_error_response):
    mock_request = httpx.Request("GET", "http://test")
    http_error = httpx.HTTPStatusError(
        "Error message", request=mock_request, response=json_error_response
    )

    @handle_errors(http_error_class=InferenceError)
    def failing_function():
        raise http_error

    with pytest.raises(InferenceError):
        failing_function()


def test_handle_errors_with_http_status_error_no_response(mocker):
    mock_request = httpx.Request("GET", "http://test")
    http_error = httpx.HTTPStatusError(
        "Error message", request=mock_request, response=None
    )

    @handle_errors()
    def failing_function():
        raise http_error

    with pytest.raises(httpx.HTTPStatusError):
        failing_function()


def test_handle_errors_with_request_error(mocker):
    request_error = httpx.RequestError("Connection failed", request=mocker.Mock())

    @handle_errors()
    def failing_function():
        raise request_error

    with pytest.raises(httpx.RequestError) as exc_info:
        failing_function()

    assert "Check network configuration" in str(exc_info.value)
    assert "retry" in str(exc_info.value).lower()


def test_handle_errors_with_http_error(mocker):
    http_error = httpx.HTTPError("HTTP error occurred")

    @handle_errors()
    def failing_function():
        raise http_error

    with pytest.raises(httpx.HTTPError) as exc_info:
        failing_function()

    assert "Check network configuration" in str(exc_info.value)
    assert "Retry again" in str(exc_info.value)


# Test InferenceError
@pytest.mark.parametrize(
    "response_fixture,has_source",
    [
        ("json_error_response", True),
        ("axum_error_response", False),
    ],
)
def test_inference_error(request, response_fixture, has_source):
    """Test InferenceError with both error structures"""
    response = request.getfixturevalue(response_fixture)
    error = InferenceError(response)

    assert error.code == 400
    assert error.error == "Bad Request"
    assert "Inference failed" in str(error)
    if has_source:
        assert "source: engine" in str(error)
    else:
        assert "source" not in str(error)


# Test InferenceTimeoutError
@pytest.mark.parametrize(
    "error_msg",
    [
        "Connection timed out",
        "Network unreachable",
        "",
    ],
)
def test_inference_timeout_error(error_msg):
    error = InferenceTimeoutError(error_msg)
    expected_msg = f"Inference failed: {error_msg}"
    assert str(error) == expected_msg


# Test ModelUploadError
@pytest.mark.parametrize(
    "response_fixture,has_source",
    [
        ("json_error_response", True),
        ("axum_error_response", False),
    ],
)
def test_model_upload_error(request, response_fixture, has_source):
    """Test ModelUploadError with both error structures"""
    response = request.getfixturevalue(response_fixture)
    error = ModelUploadError(response)

    assert error.code == 400
    assert error.error == "Bad Request"
    assert "Model failed to upload" in str(error)
    if has_source:
        assert "source: engine" in str(error)
    else:
        assert "source" not in str(error)

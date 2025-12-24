import httpx

from wallaroo.http_utils import (
    _get_base_headers,
    _setup_http_client,
)


def test_get_base_headers():
    """Test the base headers formation."""
    headers = _get_base_headers()
    assert "user-agent" in headers
    assert headers["user-agent"] == "WallarooSDK/0.0.0"
    assert "authorization" not in headers


def test_setup_http_client(mocker):
    """Test HTTP client setup with proper configuration."""
    # Mock the client
    mock_client = mocker.Mock()
    mock_client.api_endpoint = "http://test-api:8080"
    mock_client.timeout = 30
    mock_client.auth = mocker.Mock()

    # Mock httpx.Client
    mock_httpx_client = mocker.Mock()
    mocker.patch("httpx.Client", return_value=mock_httpx_client)

    # Call the function
    result = _setup_http_client(mock_client)

    # Verify the result
    assert result == mock_httpx_client

    # Verify httpx.Client was called with correct parameters
    httpx.Client.assert_called_once_with(
        base_url="http://test-api:8080",
        auth=mock_client.auth,
        headers={
            "user-agent": "WallarooSDK/0.0.0",
        },
        timeout=httpx.Timeout(30),
        limits=httpx.Limits(keepalive_expiry=30),
    )


def test_setup_http_client_with_custom_headers(mocker):
    """Test HTTP client setup with custom headers."""
    # Mock the client
    mock_client = mocker.Mock()
    mock_client.api_endpoint = "http://test-api:8080"
    mock_client.timeout = 60
    mock_client.auth = mocker.Mock()

    # Mock httpx.Client
    mock_httpx_client = mocker.Mock()
    mocker.patch("httpx.Client", return_value=mock_httpx_client)

    # Custom headers
    custom_headers = {"X-Custom": "value", "X-API-Key": "secret"}

    # Call the function
    result = _setup_http_client(mock_client, custom_headers)

    # Verify the result
    assert result == mock_httpx_client

    # Verify httpx.Client was called with merged headers
    httpx.Client.assert_called_once_with(
        base_url="http://test-api:8080",
        auth=mock_client.auth,
        headers={
            "user-agent": "WallarooSDK/0.0.0",
            "X-Custom": "value",
            "X-API-Key": "secret",
        },
        timeout=httpx.Timeout(60),
        limits=httpx.Limits(keepalive_expiry=60),
    )


def test_setup_http_client_without_custom_headers(mocker):
    """Test HTTP client setup without custom headers."""
    # Mock the client
    mock_client = mocker.Mock()
    mock_client.api_endpoint = "http://test-api:8080"
    mock_client.timeout = 45
    mock_client.auth = mocker.Mock()

    # Mock httpx.Client
    mock_httpx_client = mocker.Mock()
    mocker.patch("httpx.Client", return_value=mock_httpx_client)

    # Call the function without custom headers
    result = _setup_http_client(mock_client)

    # Verify the result
    assert result == mock_httpx_client

    # Verify httpx.Client was called with only base headers
    httpx.Client.assert_called_once_with(
        base_url="http://test-api:8080",
        auth=mock_client.auth,
        headers={
            "user-agent": "WallarooSDK/0.0.0",
        },
        timeout=httpx.Timeout(45),
        limits=httpx.Limits(keepalive_expiry=45),
    )

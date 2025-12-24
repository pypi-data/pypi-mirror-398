import os
from typing import TYPE_CHECKING, Optional

import httpx

from .version import _user_agent

if TYPE_CHECKING:
    from .client import Client


def _get_base_headers():
    return {
        "user-agent": _user_agent,
    }


def _log_httpx_request(request):
    print(f"HTTPX Request: {request.method} {request.url}")
    print("HTTPX Headers:")
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    print()
    # Check if this is a multipart request
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        print("\nHTTPX Multipart Body:")
        # Read the body content
        request.read()
        print(request.content.decode("utf-8", errors="replace"))
    print()


def _setup_http_client(
    client: "Client", headers: Optional[dict] = None
) -> "httpx.Client":
    base_headers = _get_base_headers()
    event_hooks = {}

    if os.getenv("WALLAROO_DEBUG_HTTPX"):
        event_hooks = {"request": [_log_httpx_request]}

    if headers:
        base_headers.update(headers)
    client_kwargs = {
        "base_url": client.api_endpoint,
        "auth": client.auth,
        "headers": base_headers,
        "timeout": httpx.Timeout(client.timeout),
        "limits": httpx.Limits(keepalive_expiry=client.timeout),
    }

    # Only add event_hooks if not empty
    if event_hooks:
        client_kwargs["event_hooks"] = event_hooks

    client._http_client = httpx.Client(
        **client_kwargs,
    )
    return client._http_client

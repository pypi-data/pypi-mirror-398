"""Handles authentication to the Wallaroo platform.

Performs a "device code"-style OAuth login flow.

The code is organized as follows:

* Auth objects returned by `create()` should be placed on each request to
  platform APIs. Currently, we have the following types:
  * NoAuth: Does not modify requests
  * PlatformAuth: Places `Authorization: Bearer XXX` headers on each outgoing
    request

* Objects derived from TokenFetcher know how to obtain an AccessToken from a
  particular provider:
  * KeycloakTokenFetcher: Fetches a token from Keycloak using a device code
    login flow
  * CachedTokenFetcher: Wraps another TokenFetcher and caches the value to a
    JSON file to reduce the number of user logins needed.
"""

import abc
import datetime
import enum
import json
import logging as log
import os
import pathlib
import posixpath
import shutil
import threading
import time
from typing import Any, Dict, Generator, NamedTuple, Optional, Tuple, Union

import appdirs  # type: ignore
import httpx
import jwt

from .version import _user_agent

AUTH_PATH = "WALLAROO_SDK_CREDENTIALS"
USER_VAR = "WALLAROO_USER"
PASSWORD_VAR = "WALLAROO_PASSWORD"
KEYCLOAK_CLIENT_NAME = "sdk-client"

KEYCLOAK_REALM = "master"

lock = threading.Lock()
################################################################################
# Module public API
################################################################################


class AuthType(enum.Enum):
    """Defines all the supported auth types.

    Handles conversions from string names to enum values.
    """

    NONE = "none"
    SSO = "sso"
    USER_PASSWORD = "user_password"
    TEST_AUTH = "test_auth"
    TOKEN = "token"
    ORCH = "orch"


class TokenData(NamedTuple):
    token: str
    user_email: str
    user_id: str

    def to_dict(self) -> Dict[str, str]:
        return self._asdict()


class _WallarooAuth(httpx.Auth):
    """Add a user_id function to base auth class"""

    def user_id(self) -> Optional[str]:
        pass

    def user_email(self) -> Optional[str]:
        pass

    def _bearer_token_str(self) -> Optional[str]:
        pass

    def _access_token(self) -> "_AccessToken":
        raise NotImplementedError()

    def _force_reload(self) -> None:
        pass

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Implement httpx.Auth interface"""
        yield request


def create(keycloak_addr: str, auth_type: Union[AuthType, str, None]) -> _WallarooAuth:
    """Returns an auth object of the corresponding type.

    :param str keycloak_addr: Address of the Keycloak instance to auth against
    :param AuthType or str auth_type: Type of authentication to use
    :return: Auth object that can be passed to all `httpx` calls
    :rtype: AuthBase
    :raises NotImplementedError: if auth_type is not recognized
    """
    if isinstance(auth_type, str):
        auth_type = AuthType(auth_type.lower())
    elif os.getenv(AUTH_PATH) or os.getenv(USER_VAR):
        auth_type = AuthType.USER_PASSWORD
    elif auth_type is None or auth_type == AuthType.NONE:
        return _NoAuth()
    else:
        # TODO: Error?
        print("Unknown auth type.")

    cached_token_path = (
        pathlib.Path(
            appdirs.user_cache_dir(appname="wallaroo_sdk", appauthor="wallaroo")
        )
        / "auth"
        / "keycloak.json"
    )
    fetcher: _TokenFetcher
    if auth_type == AuthType.SSO:
        fetcher = _CachedTokenFetcher(
            path=cached_token_path,
            fetcher=_KeycloakTokenFetcher(
                address=keycloak_addr,
                realm=KEYCLOAK_REALM,
                client_id=KEYCLOAK_CLIENT_NAME,
            ),
        )
    elif auth_type == AuthType.USER_PASSWORD:
        (username, password) = _GetUserPasswordCreds()
        fetcher = _CachedTokenFetcher(
            path=cached_token_path,
            fetcher=_PasswordTokenFetcher(
                address=keycloak_addr,
                realm=KEYCLOAK_REALM,
                client_id=KEYCLOAK_CLIENT_NAME,
                username=username,
                password=password,
            ),
        )
    elif auth_type == AuthType.TEST_AUTH:
        return _TestAuth()
    elif auth_type == AuthType.TOKEN:
        env_key = "WALLAROO_SDK_CREDENTIALS"
        if env_key not in os.environ:
            raise Exception("Passed token auth, but no token provided.")
        if not os.path.exists(os.environ[env_key]):
            raise Exception("Token file provided, but file does not exist.")
        data = _get_token_from_file(os.environ[env_key])
        fetcher = _RawTokenFetcher(data)
    elif auth_type == AuthType.ORCH:
        fetcher = _OfflineAccessTokenFetcher(
            fetcher=_PasswordTokenFetcher(
                address="",
                realm="",
                client_id="",
                username="",
                password="",
            ),
            path=cached_token_path,
            address=keycloak_addr,
            realm=KEYCLOAK_REALM,
            client_id=KEYCLOAK_CLIENT_NAME,
        )
    else:
        raise NotImplementedError(f"Unsupported auth type: {auth_type}")
    return _PlatformAuth(fetcher=fetcher)


def logout():
    """Removes cached values for all third-party auth providers.

    This will not invalidate auth objects already created with `create()`.

    :rtype: None
    """
    cache_dir = (
        pathlib.Path(
            appdirs.user_cache_dir(appname="wallaroo_sdk", appauthor="wallaroo")
        )
        / "auth"
    )
    shutil.rmtree(cache_dir, ignore_errors=True)


class AuthError(Exception):
    """Base type for all errors in this module."""

    def __init__(self, message: str, code: Optional[int] = None) -> None:
        if code:
            super().__init__(f"[HTTP {code}] {message}")
        else:
            super().__init__(message)


class TokenFetchError(AuthError):
    """Errors encountered while performing a login."""

    pass


class TokenRefreshError(AuthError):
    """Errors encountered while refreshing an AccessToken."""

    pass


################################################################################
# Module private classes
################################################################################


def _GetUserPasswordCreds() -> Tuple[str, str]:
    """Returns username/password credentials discovered via the environment.

    If this function is called, $WALLAROO_SDK_CREDENTIALS must point to a JSON
    file containing the following shape:

    {
        "username": "some_keycloak_username",
        "password": "some_password"
    }

    Returns: (username, password)

    Raises: TokenFetchError if the var is not set or the file is not found.
    """
    if os.getenv(USER_VAR):
        return (os.environ[USER_VAR], os.environ[PASSWORD_VAR])
    path = os.getenv(AUTH_PATH)
    if not path:
        raise TokenFetchError(f"${AUTH_PATH} is not set")
    p = pathlib.Path(path)
    if not p.is_file():
        raise TokenFetchError(f"{AUTH_PATH} does not point to a file")
    with p.open("r") as f:
        creds = json.loads(f.read())
    return (creds["username"], creds["password"])


def _get_token_from_file(path: str) -> TokenData:
    p = pathlib.Path(path)
    with p.open("r") as f:
        creds = json.loads(f.read())
    if "token" not in creds:
        raise Exception("Token property field not in json.")
    if "user_email" not in creds:
        raise Exception("User email property field not in json.")
    if "user_id" not in creds:
        raise Exception("User id property field not in json.")
    return TokenData(**creds)


class _AccessToken(NamedTuple):
    """Wraps a token returned by an oauth provider.

    These tokens require a manual (read: annoying) flow to obtain
    and either don't expire or are otherwise long-lived, so they should be
    cached aggressively.
    """

    # Token payload (e.g. "gho_qtGcULeZO3HbvCRS3tl9GR0xtO9nRQ3F" for Github)
    token: str
    # Expiry time for `token`
    expiry: datetime.datetime
    # Refresh token payload
    refresh_token: str
    # Refresh token expiry time
    refresh_token_expiry: datetime.datetime
    # User Id from keycloak
    user_id: str
    # email is from keycloak
    user_email: str

    def ToDict(self) -> Dict[str, Any]:
        return {
            "access_token": self.token,
            "expiry": self.expiry.timestamp(),
            "refresh_token": self.refresh_token,
            "refresh_token_expiry": self.refresh_token_expiry.timestamp(),
            "user_id": self.user_id,
            "user_email": self.user_email,
        }

    @classmethod
    def FromDict(cls, d):
        return cls(
            token=d["access_token"],
            expiry=datetime.datetime.fromtimestamp(d["expiry"]),
            refresh_token=d["refresh_token"],
            refresh_token_expiry=datetime.datetime.fromtimestamp(
                d["refresh_token_expiry"]
            ),
            user_id=d["user_id"],
            user_email=d["user_email"],
        )


class _TokenFetcher(abc.ABC):
    """Defines a method by which tokens are fetched."""

    @abc.abstractmethod
    def Fetch(self) -> _AccessToken:
        """Performs a third-party-specific manual flow to obtain a token.

        Raises: TokenFetchError if the flow fails.
        """
        pass

    @abc.abstractmethod
    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        """Performs a token refresh to obtain a new token.

        Raises: TokenRefreshError if the flow fails.
        """
        pass

    def Reset(self) -> None:
        """Resets any internal state.

        This can be called by higher levels before reattempting a token exchange
        if it is suspected that the fetcher is in a bad state.
        """
        pass


class _OfflineAccessTokenFetcher(_TokenFetcher):
    """Uses an offline token file for orchestration as the single refresh token"""

    def __init__(
        self,
        address: str,
        realm: str,
        client_id: str,
        path: pathlib.Path,
        fetcher: _TokenFetcher,
    ) -> None:
        self.address = address
        self.realm = realm
        self.client_id = client_id
        self.path = path
        self.fetcher = fetcher

    def Fetch(self) -> _AccessToken:
        offline_token: _AccessToken
        try:
            with self.path.open("r") as f:
                token = json.load(f, object_hook=_AccessToken.FromDict)
                offline_token = self.Refresh(token)
        except Exception as e:
            log.info(
                "Couldn't load offline access token from '%s' (%s); re-fetching",
                self.path,
                e,
            )
        return offline_token

    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        if datetime.datetime.now() < access_token.expiry - datetime.timedelta(
            seconds=10
        ):
            return access_token

        log.debug("refreshing access_token with offline token via Keycloak...")

        refresh_endpoint = posixpath.join(
            self.address,
            "auth/realms",
            self.realm,
            "protocol/openid-connect/token",
        )
        res = httpx.post(
            refresh_endpoint,
            data={
                "client_id": self.client_id,
                "grant_type": "refresh_token",
                "refresh_token": access_token.refresh_token,
            },
            headers={"User-Agent": _user_agent},
        )
        if res.status_code != 200:
            log.error(
                "Keycloak token refresh got error: %d - %s", res.status_code, res.text
            )
            raise TokenRefreshError(res.text, code=res.status_code)

        res_data = json.loads(res.text)
        decoded = jwt.decode(
            res_data["access_token"], options={"verify_signature": False}
        )
        user_id = decoded["sub"]
        user_email = decoded["email"]
        new_access_token = _AccessToken(
            token=res_data["access_token"],
            expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["expires_in"]),
            refresh_token=res_data["refresh_token"],
            refresh_token_expiry=datetime.datetime.now() + datetime.timedelta(days=30),
            user_id=user_id,
            user_email=user_email,
        )
        log.debug("keycloak offline token refresh successful")
        return new_access_token


class _CachedTokenFetcher(_TokenFetcher):
    """Wraps another TokenFetcher; persists its token to a file.

    If the file named by `path` already exists and contains a valid token, this
    TokenFetcher returns that value. If not, this TokenFetcher delegates to the
    supplied fetcher and caches that fetcher's value in said file.
    """

    def __init__(self, path: pathlib.Path, fetcher: _TokenFetcher) -> None:
        # Path to the JSON file in which AccessToken should be stored.
        self.path = path
        # Fetcher to wrap.
        self.fetcher = fetcher
        # Fetch and cache the underlying value ASAP.
        self.Fetch()

    def Fetch(self) -> _AccessToken:
        try:
            with self.path.open("r") as f:
                token = json.load(f, object_hook=_AccessToken.FromDict)
                return self.fetcher.Refresh(token)
        except Exception as e:
            log.info(
                "Couldn't load access token from '%s' (%s); re-fetching", self.path, e
            )

        access_token = self.fetcher.Fetch()
        if self.path.exists():
            self.path.unlink()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._WriteFile(access_token)
        return access_token

    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        """Refreshes the token using the underlying fetcher and saves the result."""
        access_token = self.fetcher.Refresh(access_token)
        self._WriteFile(access_token)
        return access_token

    def Reset(self) -> None:
        """Deletes the cached file before delegating to the underlying Fetcher."""
        if self.path.exists():
            self.path.unlink()
        self.fetcher.Reset()

    def _WriteFile(self, access_token: _AccessToken) -> None:
        with self.path.open("w") as f:
            f.write(json.dumps(access_token.ToDict()))
        self.path.chmod(0o600)


class _RawTokenFetcher(_TokenFetcher):
    """
    Used for passing a raw token. This is meant for nested calls, and short lived request.
    Refresh will not handled heree.
    """

    access_token: _AccessToken

    def __init__(self, token_data: TokenData) -> None:
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
        self.access_token = _AccessToken(
            expiry=expiry,
            refresh_token="unknown",
            refresh_token_expiry=expiry,
            **token_data.to_dict(),
        )

    def Fetch(self) -> _AccessToken:
        return self.access_token

    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        return self.access_token

    def Reset(self) -> None:
        return None

    def _WriteFile(self, access_token: _AccessToken) -> None:
        pass


class _KeycloakTokenFetcher(_TokenFetcher):
    def __init__(self, address: str, realm: str, client_id: str) -> None:
        self.address = address
        self.realm = realm
        self.client_id = client_id

    def Fetch(self) -> _AccessToken:
        device_code_endpoint = posixpath.join(
            self.address,
            "auth/realms",
            self.realm,
            "protocol/openid-connect/auth/device",
        )
        headers = {"User-Agent": _user_agent}
        res = httpx.post(
            device_code_endpoint,
            data={
                "client_id": self.client_id,
            },
            headers=headers,
        )
        if res.status_code != 200:
            log.error(
                "Keycloak device code fetch got error: %d - %s",
                res.status_code,
                res.text,
            )
            raise TokenFetchError(res.text, code=res.status_code)
        res_data = json.loads(res.text)
        device_code = res_data["device_code"]
        poll_interval = res_data["interval"]
        expire_time = datetime.datetime.now() + datetime.timedelta(
            seconds=int(res_data["expires_in"])
        )
        internal_auth_url = posixpath.join(self.address, "auth")
        external_auth_url = os.environ.get(
            "WALLAROO_SDK_AUTH_ENDPOINT", internal_auth_url
        )
        verification_uri_complete = res_data["verification_uri_complete"].replace(
            internal_auth_url, external_auth_url, 1
        )

        print(
            f"Please log into the following URL in a web browser:\n\n\t{verification_uri_complete}\n"
        )

        while datetime.datetime.now() < expire_time:
            log.debug("Polling Keycloak for access_code...")
            token_endpoint = posixpath.join(
                self.address,
                "auth/realms",
                self.realm,
                "protocol/openid-connect/token",
            )
            res = httpx.post(
                token_endpoint,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": self.client_id,
                },
                headers=headers,
            )
            res_data = json.loads(res.text)
            if res.status_code != 200:
                if "error" in res_data and res_data["error"] in [
                    "authorization_pending",
                    "slow_down",
                ]:
                    log.debug("keycloak authorization is still pending")
                    time.sleep(poll_interval)
                    continue
                else:
                    log.error(
                        "unknown error while polling for access_token: %d - %s",
                        res.status_code,
                        res.text,
                    )
                    raise TokenFetchError(res.text, code=res.status_code)
            log.debug("got access_token from Keycloak")
            print("Login successful!")
            decoded = jwt.decode(
                res_data["access_token"], options={"verify_signature": False}
            )
            user_id = decoded["sub"]
            user_email = decoded["email"]
            return _AccessToken(
                token=res_data["access_token"],
                expiry=datetime.datetime.now()
                + datetime.timedelta(seconds=int(res_data["expires_in"])),
                refresh_token=res_data["refresh_token"],
                refresh_token_expiry=datetime.datetime.now()
                + datetime.timedelta(seconds=int(res_data["refresh_expires_in"])),
                user_id=user_id,
                user_email=user_email,
            )

        raise TokenFetchError("Device code expired while waiting for user login")

    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        if datetime.datetime.now() < access_token.expiry - datetime.timedelta(
            seconds=10
        ):
            return access_token

        if datetime.datetime.now() >= access_token.refresh_token_expiry:
            raise TokenRefreshError("refresh token has expired")

        log.debug("refreshing access_token via Keycloak...")

        refresh_endpoint = posixpath.join(
            self.address,
            "auth/realms",
            self.realm,
            "protocol/openid-connect/token",
        )
        res = httpx.post(
            refresh_endpoint,
            data={
                "client_id": self.client_id,
                "grant_type": "refresh_token",
                "refresh_token": access_token.refresh_token,
            },
            headers={"User-Agent": _user_agent},
        )
        if res.status_code != 200:
            log.error(
                "Keycloak token refresh got error: %d - %s", res.status_code, res.text
            )
            raise TokenRefreshError(res.text, code=res.status_code)

        res_data = json.loads(res.text)
        decoded = jwt.decode(
            res_data["access_token"], options={"verify_signature": False}
        )
        user_id = decoded["sub"]
        user_email = decoded["email"]
        new_access_token = _AccessToken(
            token=res_data["access_token"],
            expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["expires_in"]),
            refresh_token=res_data["refresh_token"],
            refresh_token_expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["refresh_expires_in"]),
            user_id=user_id,
            user_email=user_email,
        )
        log.debug("keycloak token refresh successful")
        return new_access_token


class _PasswordTokenFetcher(_TokenFetcher):
    def __init__(
        self,
        address: str,
        realm: str,
        client_id: str,
        username: str,
        password: str,
    ):
        self.address = address
        self.realm = realm
        self.client_id = client_id
        self.username = username
        self.password = password

    def Fetch(self) -> _AccessToken:
        token_endpoint = posixpath.join(
            self.address,
            "auth/realms",
            self.realm,
            "protocol/openid-connect/token",
        )
        res = httpx.post(
            token_endpoint,
            data={
                "client_id": self.client_id,
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            },
            headers={"User-Agent": _user_agent},
        )
        if res.status_code != 200:
            log.error(
                "Keycloak token refresh got error: %d - %s", res.status_code, res.text
            )
            raise TokenFetchError(res.text, code=res.status_code)
        res_data = json.loads(res.text)

        decoded = jwt.decode(
            res_data["access_token"], options={"verify_signature": False}
        )
        user_id = decoded["sub"]
        user_email = decoded["email"] if "email" in decoded else "admin@keycloak"
        access_token = _AccessToken(
            token=res_data["access_token"],
            expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["expires_in"]),
            refresh_token=res_data["refresh_token"],
            refresh_token_expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["refresh_expires_in"]),
            user_id=user_id,
            user_email=user_email,
        )
        return access_token

    def Refresh(self, access_token: _AccessToken) -> _AccessToken:
        if datetime.datetime.now() < access_token.expiry - datetime.timedelta(
            seconds=10
        ):
            return access_token

        if datetime.datetime.now() >= access_token.refresh_token_expiry:
            raise TokenRefreshError("refresh token has expired")

        log.debug("refreshing access_token via Keycloak...")

        refresh_endpoint = posixpath.join(
            self.address,
            "auth/realms",
            self.realm,
            "protocol/openid-connect/token",
        )
        res = httpx.post(
            refresh_endpoint,
            data={
                "client_id": self.client_id,
                "grant_type": "refresh_token",
                "refresh_token": access_token.refresh_token,
            },
            headers={"User-Agent": _user_agent},
        )
        if res.status_code != 200:
            log.error(
                "Keycloak token refresh got error: %d - %s", res.status_code, res.text
            )
            raise TokenRefreshError(res.text, code=res.status_code)

        res_data = json.loads(res.text)
        new_access_token = _AccessToken(
            token=res_data["access_token"],
            expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["expires_in"]),
            refresh_token=res_data["refresh_token"],
            refresh_token_expiry=datetime.datetime.now()
            + datetime.timedelta(seconds=res_data["refresh_expires_in"]),
            user_id=access_token.user_id,
            user_email=access_token.user_email,
        )
        log.debug("keycloak token refresh successful")
        return new_access_token


class _NoAuth(_WallarooAuth):
    """No-op auth hook that does not change requests."""

    def __init__(self) -> None:
        pass

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Returns the request unmodified."""
        yield request

    def user_id(self) -> None:
        pass

    def user_email(self) -> str:
        return "default@ex.co"

    def _bearer_token_str(self) -> str:
        return "no token"

    def _access_token(self) -> "_AccessToken":
        return _AccessToken(
            token="definitely_an_access_token",
            expiry=datetime.datetime.now(),
            refresh_token="none",
            refresh_token_expiry=datetime.datetime.now(),
            user_email="test",
            user_id="test",
        )

    def _force_reload(self) -> None:
        return super()._force_reload()


class _PlatformAuth(_WallarooAuth):
    """Auth object for when our platform has auth enabled.

    This object should be constructed once and then passed to every `httpx`
    call as an `auth` parameter.

    Takes a TokenFetcher that will be different depending on the third-party
    provider specified.
    """

    def __init__(self, fetcher: _TokenFetcher):
        self.fetcher = fetcher

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Attaches a Keycloak JWT to the outgoing request."""
        request.headers["Authorization"] = self._bearer_token_str()
        yield request

    def auth_header(self) -> Dict[str, str]:
        headers = {}
        headers["Authorization"] = self._bearer_token_str()
        return headers

    def _bearer_token_str(self) -> str:
        """Generates a bearer string using a Keycloak JWT."""
        token = self._access_token()
        return "Bearer {}".format(token.token)

    def _access_token(self) -> "_AccessToken":
        with lock:
            try:
                token = self.fetcher.Refresh(self.fetcher.Fetch())
            except TokenRefreshError:
                # Maybe the refresh failed because the refresh token expired.
                # Re-exchange in an attempt to get a fresh JWT.
                self.fetcher.Reset()
                token = self.fetcher.Fetch()
            return token

    def _force_reload(self) -> None:
        with lock:
            token = self.fetcher.Fetch()
            # Make sure the token is expired, to cause the fetcher to bring a fresh one
            token = token._replace(expiry=datetime.datetime.now())
            try:
                self.fetcher.Refresh(token)
            except TokenRefreshError:
                # if refresh token is expired as well
                # reset auth; prompt user
                self.fetcher.Reset()

    def user_id(self) -> Optional[str]:
        return self._access_token().user_id

    def user_email(self) -> Optional[str]:
        return self._access_token().user_email


class _TestAuth(_WallarooAuth):
    """Auth type for unit tests"""

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Attaches a Keycloak JWT to the outgoing request."""
        request.headers["Authorization"] = self._bearer_token_str()
        yield request

    def user_id(self) -> Optional[str]:
        return "99cace15-e0d4-4bb6-bf14-35efee181b90"

    def user_email(self) -> Optional[str]:
        return "jane@ex.co"

    def _bearer_token_str(self) -> str:
        return "definitely_a_bearer_token_str"

    def _access_token(self) -> "_AccessToken":
        return _AccessToken(
            token="definitely_an_access_token",
            expiry=datetime.datetime.now(),
            refresh_token="none",
            refresh_token_expiry=datetime.datetime.now(),
            user_email="test",
            user_id="test",
        )

    def _force_reload(self) -> None:
        pass

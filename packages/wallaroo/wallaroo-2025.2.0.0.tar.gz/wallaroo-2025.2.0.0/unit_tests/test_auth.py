import datetime
import pathlib
import tempfile
import unittest
from unittest import mock

import httpx
import pytest
import respx

from wallaroo import auth

JWT = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJMMVBlNC0tSEo0TjMzelFqcHBfTEJQUUIzbHZ3UUQ4UDc2cUlqcFNHazZZIn0.eyJleHAiOjE2NDM5MDMwNzYsImlhdCI6MTY0MzkwMzAxNiwiYXV0aF90aW1lIjoxNjQzOTAxMDMzLCJqdGkiOiJmZmNlMjIyYS1jOGJjLTQ3M2QtYmNhYS0zYTM2YWQ0ZWJhMjAiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjkwOTAvYXV0aC9yZWFsbXMvbWFzdGVyIiwiYXVkIjpbIm1hc3Rlci1yZWFsbSIsImFjY291bnQiXSwic3ViIjoiNTkwNWMxNGYtYzcwZC00YWZiLWExZWMtOGZhNjllOGU1ZjM1IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoic2RrLWNsaWVudCIsInNlc3Npb25fc3RhdGUiOiIxNzA3YjBiMS0xYzAzLTQ2OGQtYTVhNy1hNzZkODBlNjk1YzYiLCJhY3IiOiIwIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImRlZmF1bHQtcm9sZXMtbWFzdGVyIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7Im1hc3Rlci1yZWFsbSI6eyJyb2xlcyI6WyJ2aWV3LXVzZXJzIiwicXVlcnktZ3JvdXBzIiwicXVlcnktdXNlcnMiXX0sImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS11c2VyLWlkIjoiNTkwNWMxNGYtYzcwZC00YWZiLWExZWMtOGZhNjllOGU1ZjM1IiwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLWFsbG93ZWQtcm9sZXMiOlsidXNlciJdLCJ4LWhhc3VyYS11c2VyLWdyb3VwcyI6Int9In0sIm5hbWUiOiJLZWl0aCBMb2huZXMiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJrcmxvaG5lcyIsImdpdmVuX25hbWUiOiJLZWl0aCIsImZhbWlseV9uYW1lIjoiTG9obmVzIiwiZW1haWwiOiJsb2huZXNrQGdtYWlsLmNvbSJ9.akPI9srL4WIWU8JO1qHg9D14GLGEtv_2DbVChSQ62Zs6dz92-J2HQPxwpBaoMp_gXN21WDBVl4ggVL7CSCRULp3Mcdn3ZnxKgaGr2UQEaM9tS7-fdXmld3eGy16bP0cywqrr78-w5A-Ko-wTJMr5VLPmduIthzkJVPlbR9i3bq3UmcRjoEiguJR_wez5yhaLBrFTVrUWeGyhqhAosZzdhPtWojKou_X9mTB4E2PP1Nmjoi4O3IDgZJ8VEP2fBwHpraWPN_pXbIcu_4CEfJinqanHfkVOtVSTdWxKSp4xXmvYgMApUEPP0PThHERch4uKqsstsaRCh24_AIvEq0bLPA"


def seconds_from_now(n: int) -> datetime.datetime:
    return datetime.datetime.now() + datetime.timedelta(seconds=n)


class TestKeycloakTokenFetcher:
    @respx.mock(assert_all_mocked=False)
    def test_fetch_tokenfetcherror_on_device_code_post_failure(self, respx_mock):
        # Request to Keycloak for device code fails with 404
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(return_value=httpx.Response(404))

        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )
        with pytest.raises(auth.TokenFetchError):
            access_token = token_fetcher.Fetch()
            del access_token

        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_fetch(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll for access_token for the corresponding device code succeeds immediately
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 60,
                    "refresh_token": "refresh_token_data",
                    "refresh_expires_in": 1800,
                },
            )
        )

        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )
        access_token = token_fetcher.Fetch()

        assert JWT == access_token.token
        assert "refresh_token_data" == access_token.refresh_token
        assert 2 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_fetch_poll(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Multiple polls that report the user hasn't finished the auth flow yet, then success
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            side_effect=[
                httpx.Response(
                    400,
                    json={
                        "error": "authorization_pending",
                        "error_description": "The authorization request is still pending",
                    },
                ),
                httpx.Response(
                    400,
                    json={
                        "error": "authorization_pending",
                        "error_description": "The authorization request is still pending",
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": 60,
                        "refresh_token": "refresh_token_data",
                        "refresh_expires_in": 1800,
                    },
                ),
            ]
        )

        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )
        access_token = token_fetcher.Fetch()
        assert JWT == access_token.token
        assert "refresh_token_data" == access_token.refresh_token
        assert 4 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_fetch_poll_slowdown(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll reports pending, then slow_down, then success
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            side_effect=[
                httpx.Response(
                    400,
                    json={
                        "error": "authorization_pending",
                        "error_description": "The authorization request is still pending",
                    },
                ),
                httpx.Response(
                    400,
                    json={
                        "error": "slow_down",
                        "error_description": "Slow down",
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": 60,
                        "refresh_token": "refresh_token_data",
                        "refresh_expires_in": 1800,
                    },
                ),
            ]
        )

        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )
        access_token = token_fetcher.Fetch()
        assert JWT == access_token.token
        assert "refresh_token_data" == access_token.refresh_token
        assert 4 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_not_expired(self, respx_mock):
        token = auth._AccessToken(
            token=JWT,
            expiry=seconds_from_now(15),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(30),
            user_id="some_user_id",
            user_email="meynard@tool.com",
        )
        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )

        new_token = token_fetcher.Refresh(token)

        assert token == new_token

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_expired(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 60,
                    "refresh_token": "new_refresh_token_data",
                    "refresh_expires_in": 1800,
                },
            )
        )
        token = auth._AccessToken(
            token=JWT,
            expiry=seconds_from_now(-1),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(10),
            user_id="some_user_id",
            user_email="mao@ccp.cn",
        )
        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )

        new_token = token_fetcher.Refresh(token)

        assert JWT == new_token.token
        assert "new_refresh_token_data" == new_token.refresh_token
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_error(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                400,
                json={
                    "error": "some_error",
                    "error_description": "unknown error",
                },
            )
        )
        token = auth._AccessToken(
            token=JWT,
            expiry=seconds_from_now(-1),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(10),
            user_id="some_user_id",
            user_email="rms@fsf.org",
        )
        token_fetcher = auth._KeycloakTokenFetcher(
            address="http://keycloak.wallaroo", realm="master", client_id="unit-tests"
        )

        with pytest.raises(auth.TokenRefreshError):
            new_token = token_fetcher.Refresh(token)
            del new_token


class TestNoAuth:
    def test_call(self):
        a = auth._NoAuth()
        req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")

        new_req = next(a.auth_flow(req))

        assert new_req == req


class TestPlatformAuth:
    @respx.mock(assert_all_mocked=False)
    def test_call(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll for access_token for the corresponding device code succeeds immediately
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 60,
                    "refresh_token": "refresh_token_data",
                    "refresh_expires_in": 1800,
                },
            )
        )
        a = auth._PlatformAuth(
            fetcher=auth._KeycloakTokenFetcher(
                address="http://keycloak.wallaroo",
                realm="master",
                client_id="unit-tests",
            )
        )
        # Creation of the above auth object should not trigger any requests.
        assert 0 == len(respx_mock.calls)

        req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")
        new_req = next(a.auth_flow(req))

        # Fetch triggered
        assert 2 == len(respx_mock.calls)

        assert f"Bearer {JWT}" == new_req.headers["Authorization"]

    @respx.mock(assert_all_mocked=False)
    def test_call_with_refresh(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll for access_token for the corresponding device code succeeds
        # immediately, with an old token, then refresh response
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": -1,
                        "refresh_token": "refresh_token_data",
                        "refresh_expires_in": 1800,
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": 60,
                        "refresh_token": "new_refresh_token_data",
                        "refresh_expires_in": 1800,
                    },
                ),
            ]
        )
        a = auth._PlatformAuth(
            fetcher=auth._KeycloakTokenFetcher(
                address="http://keycloak.wallaroo",
                realm="master",
                client_id="unit-tests",
            )
        )
        # Creation of the above auth object should not trigger any requests.
        assert 0 == len(respx_mock.calls)
        req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")
        new_req = next(a.auth_flow(req))

        # Fetch triggered
        assert 3 == len(respx_mock.calls)
        assert f"Bearer {JWT}" == new_req.headers["Authorization"]

    @respx.mock(assert_all_mocked=False)
    def test_call_with_refresh_error(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll for access_token for the corresponding device code succeeds
        # immediately, with an old token and old refresh token, then fresh token
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": -1,
                        "refresh_token": "refresh_token_data",
                        "refresh_expires_in": -1,
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "access_token": JWT,
                        "expires_in": 5,
                        "refresh_token": "new_refresh_token_data",
                        "refresh_expires_in": 5,
                    },
                ),
            ]
        )

        a = auth._PlatformAuth(
            fetcher=auth._KeycloakTokenFetcher(
                address="http://keycloak.wallaroo",
                realm="master",
                client_id="unit-tests",
            )
        )
        # Creation of the above auth object should not trigger any requests.
        assert 0 == len(respx_mock.calls)

        req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")
        new_req = next(a.auth_flow(req))

        # Device code fetch, access token fetch (pre-expired), device code
        # fetch, access token fetch
        assert 4 == len(respx_mock.calls)
        assert f"Bearer {JWT}" == new_req.headers["Authorization"]

    @respx.mock(assert_all_called=False)
    def test_call_cached(self, respx_mock):
        # Request to Keycloak for device code succeeds
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "H4NYOYjN8Ut9axie2c7jXte5qAWv7uO3Wlyraz1IhwQ",
                    "user_code": "HEUR-GINT",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=HEUR-GINT",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )
        # Poll for access_token for the corresponding device code succeeds immediately
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 60,
                    "refresh_token": "refresh_token_data",
                    "refresh_expires_in": 1800,
                },
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            a = auth._PlatformAuth(
                fetcher=auth._CachedTokenFetcher(
                    path=pathlib.Path(tmpdir) / "auth.json",
                    fetcher=auth._KeycloakTokenFetcher(
                        address="http://keycloak.wallaroo",
                        realm="master",
                        client_id="unit-tests",
                    ),
                )
            )
            # Creation of the above auth object should trigger a fetch
            assert 2 == len(respx_mock.calls)
            respx_mock.reset()

            req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")
            new_req = next(a.auth_flow(req))

            assert f"Bearer {JWT}" == new_req.headers["Authorization"]
            # Token is cached; no need to perform any fetches
            assert 0 == len(respx_mock.calls)

            a = auth._PlatformAuth(
                fetcher=auth._CachedTokenFetcher(
                    path=pathlib.Path(tmpdir) / "auth.json",
                    fetcher=auth._KeycloakTokenFetcher(
                        address="http://keycloak.wallaroo",
                        realm="master",
                        client_id="unit-tests",
                    ),
                )
            )
            # Token is still cached; no need to perform any fetches
            assert 0 == len(respx_mock.calls)
            req = httpx.Request("GET", "http://api-lb.wallaroo/v1/graphql")
            new_req = next(a.auth_flow(req))
            assert 0 == len(respx_mock.calls)


class TestCachedTokenFetcher:
    def test_fetch_on_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = mock.MagicMock(spec=auth._TokenFetcher)
            fetcher.Fetch.return_value = auth._AccessToken(
                token=JWT,
                expiry=seconds_from_now(1),
                refresh_token="refresh_token_data",
                refresh_token_expiry=seconds_from_now(1),
                user_id="some_user_id",
                user_email="larry@oracle.com",
            )
            cached_fetcher = auth._CachedTokenFetcher(
                path=pathlib.Path(tmpdir) / "auth.json", fetcher=fetcher
            )

            assert 1 == fetcher.Fetch.call_count


class TestPasswordTokenFetcher:
    @respx.mock(assert_all_mocked=False)
    def test_fetch_success(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 5,
                    "refresh_token": "refresh_token_data",
                    "refresh_expires_in": 5,
                },
            )
        )
        token_fetcher = auth._PasswordTokenFetcher(
            address="http://keycloak.wallaroo",
            realm="master",
            client_id="unit-tests",
            username="some-user",
            password="some-password",
        )

        token = token_fetcher.Fetch()

        assert JWT == token.token
        assert "refresh_token_data" == token.refresh_token
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_fetch_fail(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_grant",
                    "error_description": "Invalid user credentials",
                },
            )
        )
        token_fetcher = auth._PasswordTokenFetcher(
            address="http://keycloak.wallaroo",
            realm="master",
            client_id="unit-tests",
            username="some-user",
            password="some-password",
        )

        with pytest.raises(auth.TokenFetchError):
            token = token_fetcher.Fetch()
            del token

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_not_expired(self, respx_mock):
        token = auth._AccessToken(
            token=JWT,
            expiry=seconds_from_now(15),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(30),
            user_id="some_user_id",
            user_email="billg@msncom",
        )
        token_fetcher = auth._PasswordTokenFetcher(
            address="http://keycloak.wallaroo",
            realm="master",
            client_id="unit-tests",
            username="some-user",
            password="some-password",
        )

        new_token = token_fetcher.Refresh(token)

        assert token == new_token

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_expired(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 60,
                    "refresh_token": "new_refresh_token_data",
                    "refresh_expires_in": 1800,
                },
            )
        )
        token = auth._AccessToken(
            token="token_1_data",
            expiry=seconds_from_now(-1),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(10),
            user_id="some_user_id",
            user_email="vid@wallaroo.ai",
        )
        token_fetcher = auth._PasswordTokenFetcher(
            address="http://keycloak.wallaroo",
            realm="master",
            client_id="unit-tests",
            username="some-user",
            password="some-password",
        )

        new_token = token_fetcher.Refresh(token)

        assert JWT == new_token.token
        assert "new_refresh_token_data" == new_token.refresh_token
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_refresh_token_error(self, respx_mock):
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                400,
                json={
                    "error": "some_error",
                    "error_description": "unknown error",
                },
            )
        )
        token = auth._AccessToken(
            token="token_1_data",
            expiry=seconds_from_now(-1),
            refresh_token="refresh_token_1_data",
            refresh_token_expiry=seconds_from_now(10),
            user_id="some_user_id",
            user_email="obama@wh.gov",
        )
        token_fetcher = auth._PasswordTokenFetcher(
            address="http://keycloak.wallaroo",
            realm="master",
            client_id="unit-tests",
            username="some-user",
            password="some-password",
        )

        with pytest.raises(auth.TokenRefreshError):
            new_token = token_fetcher.Refresh(token)
            del new_token

    @respx.mock(assert_all_mocked=False)
    def test_url_replacement_with_auth_endpoint_no_duplication(self, respx_mock):
        """Test that WALLAROO_SDK_AUTH_ENDPOINT ending with /auth doesn't create duplicate /auth/ paths."""

        # Mock the device code request
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/auth/device",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "test-device-code",
                    "user_code": "TEST-CODE",
                    "verification_uri": "http://keycloak.wallaroo/auth/realms/master/device",
                    "verification_uri_complete": "http://keycloak.wallaroo/auth/realms/master/device?user_code=TEST-CODE",
                    "expires_in": 5,
                    "interval": 0,
                },
            )
        )

        # Mock the token polling request that will succeed immediately
        respx_mock.post(
            "http://keycloak.wallaroo/auth/realms/master/protocol/openid-connect/token",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": JWT,
                    "expires_in": 300,
                    "refresh_expires_in": 1800,
                    "refresh_token": "refresh-token",
                    "token_type": "bearer",
                },
            )
        )

        # Test the scenario where WALLAROO_SDK_AUTH_ENDPOINT includes /auth
        with mock.patch.dict(
            "os.environ",
            {"WALLAROO_SDK_AUTH_ENDPOINT": "http://keycloak.wallaroo/auth"},
        ):
            # Capture printed output to verify the URL
            with mock.patch("builtins.print") as mock_print:
                token_fetcher = auth._KeycloakTokenFetcher(
                    address="http://keycloak.wallaroo",  # Base URL without /auth
                    realm="master",
                    client_id="unit-tests",
                )

                access_token = token_fetcher.Fetch()

                # Verify we got a valid token
                assert access_token.token == JWT

                # Check that the printed URL doesn't have duplicate /auth/
                print_calls = [
                    call.args[0]
                    for call in mock_print.call_args_list
                    if "Please log into the following URL" in str(call.args[0])
                ]

                assert len(print_calls) > 0, "Should have printed login URL"
                login_message = print_calls[0]

                # Extract the URL from the message
                import re

                url_match = re.search(r"https?://[^\s\n]+", login_message)
                assert url_match, f"Should contain a URL in: {login_message}"

                actual_url = url_match.group(0)

                # The URL should NOT contain duplicate /auth/auth/
                assert (
                    "/auth/auth/" not in actual_url
                ), f"URL contains duplicate /auth/: {actual_url}"

                # The URL should be the correct Keycloak device URL
                expected_url = "http://keycloak.wallaroo/auth/realms/master/device?user_code=TEST-CODE"
                assert (
                    actual_url == expected_url
                ), f"Expected {expected_url}, got {actual_url}"

    def test_url_replacement_logic_comparison(self):
        """Test that demonstrates the old broken logic vs the current fixed logic."""

        # Simulate the exact scenario from the original issue
        verification_uri_complete = (
            "http://keycloak.wallaroo/auth/realms/master/device?user_code=TEST-CODE"
        )
        self_address = "http://keycloak.wallaroo"  # Base URL
        external_url = "http://keycloak.wallaroo/auth"  # External URL with /auth

        # OLD BROKEN LOGIC: Simple string replacement
        old_broken_result = verification_uri_complete.replace(
            self_address, external_url, 1
        )

        # This would create the duplicate /auth/ issue
        expected_broken_url = "http://keycloak.wallaroo/auth/auth/realms/master/device?user_code=TEST-CODE"
        assert (
            old_broken_result == expected_broken_url
        ), "Old logic should create duplicate /auth/"
        assert "/auth/auth/" in old_broken_result, "Old logic creates duplicate /auth/"

        # CURRENT FIXED LOGIC: Build internal_auth_url first, then replace
        import posixpath

        internal_auth_url = posixpath.join(
            self_address, "auth"
        )  # "http://keycloak.wallaroo/auth"
        fixed_result = verification_uri_complete.replace(
            internal_auth_url, external_url, 1
        )

        # The fixed logic should NOT create duplicates (it's a no-op when they're the same)
        expected_fixed_url = (
            "http://keycloak.wallaroo/auth/realms/master/device?user_code=TEST-CODE"
        )
        assert (
            fixed_result == expected_fixed_url
        ), "Fixed logic should not create duplicates"
        assert (
            "/auth/auth/" not in fixed_result
        ), "Fixed logic should not have duplicate /auth/"


if __name__ == "__main__":
    unittest.main()

from typing import TYPE_CHECKING, Any, Dict

from wallaroo.utils import _unwrap

from .object import UserLimitError

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class User:
    """A platform User."""

    def __init__(self, client, data: Dict[str, Any]) -> None:
        self.client = client
        self._id = data["id"]
        self._email = data["email"] if "email" in data else "admin@keycloak"
        self._username = data["username"]
        self._enabled = data["enabled"]
        self._createdTimeastamp = data["createdTimestamp"]

    def __repr__(self):
        return f"""User({{"id": "{self.id()}", "email": "{self.email()}", "username": "{self.username()}", "enabled": "{self.enabled()}")"""

    def id(self) -> str:
        return self._id

    def email(self) -> str:
        return self._email

    def username(self) -> str:
        return self._username

    def enabled(self) -> bool:
        return self._enabled

    @staticmethod
    def list_users(client):
        """List all users using the provided client."""
        users = client.httpx_client.post(
            "/v1/api/users/query",
            json={},
        )

        if users.status_code > 299:
            raise Exception("Failed to list exiting users.")
        return users.json()["users"].values()

    @staticmethod
    def get_email_by_id(
        client: "Client",
        id: str,
    ):
        from wallaroo.wallaroo_ml_ops_api_client.api.user.users_query import (
            UsersQueryBody,
            sync_detailed,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.users_query_response_200 import (
            UsersQueryResponse200,
        )

        r = sync_detailed(client=client.mlops(), body=UsersQueryBody([id]))

        if isinstance(r.parsed, UsersQueryResponse200):
            return _unwrap(r.parsed.users[id])["email"]

        raise Exception("Failed to get user information.", r)

    @staticmethod
    def invite_user(client, email, password):
        # Reuse list_users to avoid duplicate HTTP requests
        existing_users = list(User.list_users(client))
        user_present = [user for user in existing_users if user["username"] == email]

        if len(user_present) == 0:
            data = {"email": email}
            if password:
                data["password"] = password

            response = client.httpx_client.post("/v1/api/users/invite", json=data)
            if response.status_code == 403:
                raise UserLimitError()
            if response.status_code != 200:
                raise Exception("Failed to invite user")

            user = response.json()
            return user
        else:
            return user_present[0]

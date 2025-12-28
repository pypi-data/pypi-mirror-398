"""This module features the ServerConfig class, for specifying the server
configuration."""

from ipaddress import IPv4Address

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """This class implements the ServerConfig class, for specifying the connection
    configuration for a server."""

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )

    host: str = Field(default="0.0.0.0", description="The host to serve the model on")
    port: int = Field(default=8080, description="The port to serve the model on")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        """Validate host."""
        try:
            IPv4Address(value)
            return value
        except ValueError as error:
            raise ValueError("Invalid IP address") from error

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        """Validate port."""
        if not isinstance(value, int) or value <= 0 or value > 65535:
            raise ValueError("Invalid port number")
        return value

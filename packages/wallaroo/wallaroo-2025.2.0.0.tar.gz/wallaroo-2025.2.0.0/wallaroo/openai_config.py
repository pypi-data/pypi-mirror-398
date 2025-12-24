from pydantic import BaseModel, Field


class OpenaiConfig(BaseModel):
    enabled: bool = Field(
        default=False,
        description="Whether to enable OpenAI integration.",
    )
    completion_config: dict = Field(
        default={},
        description="Configuration for OpenAI completion requests.",
    )
    chat_completion_config: dict = Field(
        default={},
        description="Configuration for OpenAI chat completion requests.",
    )

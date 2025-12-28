from pydantic import BaseModel, Field


class ContinuousBatchingConfig(BaseModel):
    max_concurrent_batch_size: int = Field(
        default=1, gt=0, description="The maximum size of concurrent batches allowed."
    )

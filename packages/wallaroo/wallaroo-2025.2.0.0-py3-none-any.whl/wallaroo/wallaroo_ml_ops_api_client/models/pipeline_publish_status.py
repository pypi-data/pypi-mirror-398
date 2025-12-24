from enum import Enum


class PipelinePublishStatus(str, Enum):
    ERROR = "Error"
    PENDINGPUBLISH = "PendingPublish"
    PUBLISHED = "Published"
    PUBLISHING = "Publishing"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class ProjectPublicProjectType(str, Enum):
    FREE = "free"
    LIVE = "live"

    def __str__(self) -> str:
        return str(self.value)

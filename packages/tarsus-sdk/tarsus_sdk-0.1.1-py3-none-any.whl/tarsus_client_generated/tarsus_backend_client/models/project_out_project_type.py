from enum import Enum


class ProjectOutProjectType(str, Enum):
    FREE = "free"
    LIVE = "live"

    def __str__(self) -> str:
        return str(self.value)

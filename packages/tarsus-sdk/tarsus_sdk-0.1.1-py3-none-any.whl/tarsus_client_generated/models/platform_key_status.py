from enum import Enum


class PlatformKeyStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    TESTING = "testing"

    def __str__(self) -> str:
        return str(self.value)

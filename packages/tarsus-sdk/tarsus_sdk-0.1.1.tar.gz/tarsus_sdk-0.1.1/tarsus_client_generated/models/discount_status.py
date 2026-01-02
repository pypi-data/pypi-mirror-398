from enum import Enum


class DiscountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    EXPIRED = "EXPIRED"

    def __str__(self) -> str:
        return str(self.value)

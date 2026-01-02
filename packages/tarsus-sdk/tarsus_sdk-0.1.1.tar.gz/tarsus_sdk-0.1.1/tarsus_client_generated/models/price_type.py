from enum import Enum


class PriceType(str, Enum):
    FIXED_AMOUNT = "FIXED_AMOUNT"
    PERCENTAGE = "PERCENTAGE"

    def __str__(self) -> str:
        return str(self.value)

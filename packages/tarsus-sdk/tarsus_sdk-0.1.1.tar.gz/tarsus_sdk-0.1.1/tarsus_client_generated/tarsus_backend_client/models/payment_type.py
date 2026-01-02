from enum import Enum


class PaymentType(str, Enum):
    ONE_TIME = "ONE_TIME"
    RECURRING = "RECURRING"

    def __str__(self) -> str:
        return str(self.value)

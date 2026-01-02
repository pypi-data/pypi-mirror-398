from enum import Enum


class ServiceBillingType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"

    def __str__(self) -> str:
        return str(self.value)

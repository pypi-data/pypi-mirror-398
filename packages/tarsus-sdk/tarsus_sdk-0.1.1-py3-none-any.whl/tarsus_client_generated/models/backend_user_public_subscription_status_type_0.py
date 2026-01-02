from enum import Enum


class BackendUserPublicSubscriptionStatusType0(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

    def __str__(self) -> str:
        return str(self.value)

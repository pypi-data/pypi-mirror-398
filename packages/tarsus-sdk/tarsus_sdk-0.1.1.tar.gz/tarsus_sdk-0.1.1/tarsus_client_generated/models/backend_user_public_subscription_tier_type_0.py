from enum import Enum


class BackendUserPublicSubscriptionTierType0(str, Enum):
    ENTERPRISE = "enterprise"
    FREE = "free"
    PRO = "pro"
    STARTER = "starter"

    def __str__(self) -> str:
        return str(self.value)

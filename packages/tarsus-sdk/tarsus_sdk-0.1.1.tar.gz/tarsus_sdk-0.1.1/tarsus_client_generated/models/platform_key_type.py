from enum import Enum


class PlatformKeyType(str, Enum):
    PAYMENT_LIVE = "payment_live"
    PAYMENT_SANDBOX = "payment_sandbox"
    SHIPPING_SANDBOX = "shipping_sandbox"

    def __str__(self) -> str:
        return str(self.value)

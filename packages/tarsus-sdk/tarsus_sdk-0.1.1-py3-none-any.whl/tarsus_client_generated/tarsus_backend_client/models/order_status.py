from enum import Enum


class OrderStatus(str, Enum):
    CANCELLED = "cancelled"
    DELIVERED = "delivered"
    DISPUTED = "disputed"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    PAYMENT_FAILED = "payment_failed"
    PENDING = "pending"
    PROCESSING = "processing"
    REFUNDED = "refunded"
    SHIPPED = "shipped"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class UserPublicRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    STAFF = "staff"

    def __str__(self) -> str:
        return str(self.value)

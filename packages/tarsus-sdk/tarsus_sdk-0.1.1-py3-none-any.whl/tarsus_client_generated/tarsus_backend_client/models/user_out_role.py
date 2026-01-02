from enum import Enum


class UserOutRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    STAFF = "staff"

    def __str__(self) -> str:
        return str(self.value)

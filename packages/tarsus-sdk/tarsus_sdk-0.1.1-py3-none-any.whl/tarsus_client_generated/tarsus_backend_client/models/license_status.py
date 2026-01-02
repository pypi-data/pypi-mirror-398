from enum import Enum


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INACTIVE = "inactive"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class BackendUserPublicRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    SUPER_ADMIN = "super_admin"

    def __str__(self) -> str:
        return str(self.value)

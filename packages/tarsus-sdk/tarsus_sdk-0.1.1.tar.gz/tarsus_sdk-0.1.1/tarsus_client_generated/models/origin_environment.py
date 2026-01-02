from enum import Enum


class OriginEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

    def __str__(self) -> str:
        return str(self.value)

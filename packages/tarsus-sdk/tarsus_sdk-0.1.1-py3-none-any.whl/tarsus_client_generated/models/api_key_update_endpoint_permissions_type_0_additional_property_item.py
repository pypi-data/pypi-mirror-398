from enum import Enum


class APIKeyUpdateEndpointPermissionsType0AdditionalPropertyItem(str, Enum):
    READ = "read"
    WRITE = "write"

    def __str__(self) -> str:
        return str(self.value)

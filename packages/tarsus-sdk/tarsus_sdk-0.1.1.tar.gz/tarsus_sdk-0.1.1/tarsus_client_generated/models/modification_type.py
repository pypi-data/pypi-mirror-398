from enum import Enum


class ModificationType(str, Enum):
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    FILE_UPLOAD = "file_upload"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)

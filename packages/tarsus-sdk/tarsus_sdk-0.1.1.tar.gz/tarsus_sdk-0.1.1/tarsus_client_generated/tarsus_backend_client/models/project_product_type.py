from enum import Enum


class ProjectProductType(str, Enum):
    CUSTOMIZED_DIGITAL = "CUSTOMIZED_DIGITAL"
    CUSTOMIZED_PHYSICAL = "CUSTOMIZED_PHYSICAL"
    SERVICES = "SERVICES"
    STANDARD_DIGITAL = "STANDARD_DIGITAL"
    STANDARD_PHYSICAL = "STANDARD_PHYSICAL"

    def __str__(self) -> str:
        return str(self.value)

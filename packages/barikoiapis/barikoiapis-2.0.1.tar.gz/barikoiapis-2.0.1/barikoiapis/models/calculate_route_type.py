from enum import Enum


class CalculateRouteType(str, Enum):
    GH = "gh"

    def __str__(self) -> str:
        return str(self.value)

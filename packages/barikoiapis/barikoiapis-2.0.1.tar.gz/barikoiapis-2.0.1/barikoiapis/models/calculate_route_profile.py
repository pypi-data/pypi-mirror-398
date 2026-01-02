from enum import Enum


class CalculateRouteProfile(str, Enum):
    BIKE = "bike"
    CAR = "car"
    MOTORCYCLE = "motorcycle"

    def __str__(self) -> str:
        return str(self.value)

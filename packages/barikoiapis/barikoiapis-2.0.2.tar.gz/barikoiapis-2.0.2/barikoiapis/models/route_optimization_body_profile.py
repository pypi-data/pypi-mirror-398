from enum import Enum


class RouteOptimizationBodyProfile(str, Enum):
    BIKE = "bike"
    CAR = "car"
    FOOT = "foot"
    MOTORCYCLE = "motorcycle"

    def __str__(self) -> str:
        return str(self.value)

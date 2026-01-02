from enum import Enum


class RouteOverviewProfile(str, Enum):
    CAR = "car"
    FOOT = "foot"

    def __str__(self) -> str:
        return str(self.value)

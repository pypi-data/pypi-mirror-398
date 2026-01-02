from enum import Enum


class SnapToRoadSuccessType(str, Enum):
    POINT = "Point"

    def __str__(self) -> str:
        return str(self.value)

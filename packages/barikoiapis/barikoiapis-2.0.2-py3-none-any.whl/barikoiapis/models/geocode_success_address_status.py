from enum import Enum


class GeocodeSuccessAddressStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"

    def __str__(self) -> str:
        return str(self.value)

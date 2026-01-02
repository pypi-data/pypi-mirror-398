from enum import Enum


class RouteOverviewGeometries(str, Enum):
    GEOJSON = "geojson"
    POLYLINE = "polyline"
    POLYLINE6 = "polyline6"

    def __str__(self) -> str:
        return str(self.value)

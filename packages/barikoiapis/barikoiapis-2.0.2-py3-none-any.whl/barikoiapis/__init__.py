from dataclasses import dataclass
from typing import Optional, TypeVar, Generic, Any
from .models.calculate_route_body import CalculateRouteBody
from .models.calculate_route_body_data import CalculateRouteBodyData
from .models.calculate_route_body_data_start import CalculateRouteBodyDataStart
from .models.calculate_route_body_data_destination import CalculateRouteBodyDataDestination
from .models.calculate_route_type import CalculateRouteType
from .models.calculate_route_profile import CalculateRouteProfile
from .types import UNSET

from .models.geocode_body import GeocodeBody
from .models.geocode_body_district import GeocodeBodyDistrict
from .models.geocode_body_bangla import GeocodeBodyBangla
from .models.geocode_body_thana import GeocodeBodyThana
from .models.route_overview_geometries import RouteOverviewGeometries


from .client import Client

# ---- API imports (generated) ----
from .api.v2_0 import (
    autocomplete as _autocomplete,
    reverse_geocode as _reverse_geocode,
    nearby as _nearby,
    geocode as _geocode,
    search_place as _search_place,
    place_details as _place_details,
    route_overview as _route_overview,
    calculate_route as _calculate_route,
    snap_to_road as _snap_to_road,
    check_nearby as _check_nearby,
)

# ---- Models ----
from .models.geocode_body import GeocodeBody
from .models.calculate_route_body import CalculateRouteBody
from .models.calculate_route_body_data import CalculateRouteBodyData

T = TypeVar("T")


@dataclass
class APIResponse(Generic[T]):
    data: Optional[T]


__all__ = ["BarikoiClient"]
__version__ = "2.0.0"


class BarikoiClient:
    """
    Pythonic Barikoi SDK
    """

    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self._client = Client(
            base_url="https://barikoi.xyz",
            timeout=timeout,
        )

    # --------------------------------------------------
    # Autocomplete
    # --------------------------------------------------
    def autocomplete(
        self,
        *,
        q: str,
        bangla: bool | None = None
    ) -> APIResponse:
        return APIResponse(
            _autocomplete.sync(
                client=self._client,
                api_key=self.api_key,
                q=q,
                bangla=bangla
            )
        )

    # --------------------------------------------------
    # Reverse Geocode
    # --------------------------------------------------
    def reverseGeocode(
        self,
        *,
        latitude: float,
        longitude: float,
        district: bool | None = None,
        bangla: bool | None = None,
    ) -> APIResponse:
        return APIResponse(
            _reverse_geocode.sync(
                client=self._client,
                api_key=self.api_key,
                latitude=latitude,
                longitude=longitude,
                district=district,
                bangla=bangla,
            )
        )

    # --------------------------------------------------
    # Nearby Places
    # --------------------------------------------------
    def nearbyPlaces(
        self,
        *,
        latitude: float,
        longitude: float,
        radius: float,
        limit: int | None = None,
    ) -> APIResponse:
        return APIResponse(
            _nearby.sync(
                client=self._client,
                api_key=self.api_key,
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                limit=limit,
            )
        )

    # --------------------------------------------------
    # Rupantor Geocode (FORM DATA)
    # --------------------------------------------------
    def geocode(
        self,
        q: str,
        thana: str | None = None,
        district: str | None = None,
        bangla: str | None = None,
    ):
        """
        Geocode an address using Rupantor Geocoder.

        Args:
            q: The address to geocode.
            thana: Optional, 'yes' or 'no' to include thana info.
            district: Optional, 'yes' or 'no' to include district info.
            bangla: Optional, 'yes' or 'no' to return address in Bangla.

        Returns:
            APIResponse containing geocoding result.
        """
        body = GeocodeBody(
            q=q,
            thana=GeocodeBodyThana(thana) if thana else UNSET,
            district=GeocodeBodyDistrict(district) if district else UNSET,
            bangla=GeocodeBodyBangla(bangla) if bangla else UNSET,
        )

        result = _geocode.sync(client=self._client, api_key=self.api_key, body=body)
        return APIResponse(result)

    # --------------------------------------------------
    # Search Place
    # --------------------------------------------------
    def searchPlace(
        self,
        *,
        q: str,
    ) -> APIResponse:
        return APIResponse(
            _search_place.sync(
                client=self._client,
                api_key=self.api_key,
                q=q
            )
        )

    # --------------------------------------------------
    # Place Details
    # --------------------------------------------------
    def placeDetails(
        self,
        *,
        place_code: str,
        session_id: str | None = None,
    ) -> APIResponse:
        return APIResponse(
            _place_details.sync(
                client=self._client,
                api_key=self.api_key,
                place_code=place_code,
                session_id=session_id,

            )
        )

    # --------------------------------------------------
    # Route Overview
    # --------------------------------------------------
    def routeOverview(
        self,
        *,
        coordinates: str,
        geometries: str = "geojson",
    ) -> APIResponse:
        geometries_enum = RouteOverviewGeometries(geometries)
        return APIResponse(
            _route_overview.sync_detailed(
                client=self._client,
                api_key=self.api_key,
                coordinates=coordinates,
                geometries=geometries_enum,  # ✅ ENUM, not str
            )
        )
    # --------------------------------------------------
    # Calculate Route
    # --------------------------------------------------


    def calculateRoute(
        self,
        *,
        start: dict,
        destination: dict,
        type: str = "gh",
        profile: str = "car",
    ) -> APIResponse:
        start_model = CalculateRouteBodyDataStart(
            latitude=start["latitude"],
            longitude=start["longitude"],
        )

        destination_model = CalculateRouteBodyDataDestination(
            latitude=destination["latitude"],
            longitude=destination["longitude"],
        )

        data = CalculateRouteBodyData(
            start=start_model,
            destination=destination_model,
        )

        body = CalculateRouteBody(data=data)

        result = _calculate_route.sync_detailed(
            client=self._client,
            api_key=self.api_key,
            body=body,
            type_=CalculateRouteType(type),
            profile=CalculateRouteProfile(profile),
        )

        return APIResponse(result)


    # --------------------------------------------------
    # Snap to Road
    # --------------------------------------------------
    def snapToRoad(
        self,
        *,
        point: str,
    ) -> APIResponse:
        return APIResponse(
            _snap_to_road.sync(
                client=self._client,
                api_key=self.api_key,
                point=point,
        )
        )

    # --------------------------------------------------
    # Check Nearby
    # --------------------------------------------------
    def checkNearby(
        self,
        *,
        current_latitude: float,
        current_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
        radius: float,
    ) -> APIResponse:
        return APIResponse(
            _check_nearby.sync(
                client=self._client,
                api_key=self.api_key,
                current_latitude=current_latitude,
                current_longitude=current_longitude,
                destination_latitude=destination_latitude,
                destination_longitude=destination_longitude,
                radius=radius,
            )
        )

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.route_optimization_body_profile import RouteOptimizationBodyProfile
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.route_optimization_body_geo_points_item import RouteOptimizationBodyGeoPointsItem


T = TypeVar("T", bound="RouteOptimizationBody")


@_attrs_define
class RouteOptimizationBody:
    """
    Attributes:
        api_key (str):
        source (str): Format: latitude,longitude Example: 23.746086,90.37368.
        destination (str): Format: latitude,longitude Example: 23.746214,90.371654.
        geo_points (list[RouteOptimizationBodyGeoPointsItem]):
        profile (RouteOptimizationBodyProfile | Unset):  Default: RouteOptimizationBodyProfile.CAR.
    """

    api_key: str
    source: str
    destination: str
    geo_points: list[RouteOptimizationBodyGeoPointsItem]
    profile: RouteOptimizationBodyProfile | Unset = RouteOptimizationBodyProfile.CAR
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_key = self.api_key

        source = self.source

        destination = self.destination

        geo_points = []
        for geo_points_item_data in self.geo_points:
            geo_points_item = geo_points_item_data.to_dict()
            geo_points.append(geo_points_item)

        profile: str | Unset = UNSET
        if not isinstance(self.profile, Unset):
            profile = self.profile.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_key": api_key,
                "source": source,
                "destination": destination,
                "geo_points": geo_points,
            }
        )
        if profile is not UNSET:
            field_dict["profile"] = profile

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.route_optimization_body_geo_points_item import RouteOptimizationBodyGeoPointsItem

        d = dict(src_dict)
        api_key = d.pop("api_key")

        source = d.pop("source")

        destination = d.pop("destination")

        geo_points = []
        _geo_points = d.pop("geo_points")
        for geo_points_item_data in _geo_points:
            geo_points_item = RouteOptimizationBodyGeoPointsItem.from_dict(geo_points_item_data)

            geo_points.append(geo_points_item)

        _profile = d.pop("profile", UNSET)
        profile: RouteOptimizationBodyProfile | Unset
        if isinstance(_profile, Unset):
            profile = UNSET
        else:
            profile = RouteOptimizationBodyProfile(_profile)

        route_optimization_body = cls(
            api_key=api_key,
            source=source,
            destination=destination,
            geo_points=geo_points,
            profile=profile,
        )

        route_optimization_body.additional_properties = d
        return route_optimization_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

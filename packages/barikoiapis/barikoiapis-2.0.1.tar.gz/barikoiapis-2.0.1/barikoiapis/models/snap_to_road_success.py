from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.snap_to_road_success_type import SnapToRoadSuccessType
from ..types import UNSET, Unset

T = TypeVar("T", bound="SnapToRoadSuccess")


@_attrs_define
class SnapToRoadSuccess:
    """
    Attributes:
        coordinates (list[float] | Unset):  Example: [90.36288583910802, 23.80475086627028].
        distance (float | Unset): Distance in meters Example: 0.5866113852736488.
        type_ (SnapToRoadSuccessType | Unset):  Example: Point.
    """

    coordinates: list[float] | Unset = UNSET
    distance: float | Unset = UNSET
    type_: SnapToRoadSuccessType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        coordinates: list[float] | Unset = UNSET
        if not isinstance(self.coordinates, Unset):
            coordinates = self.coordinates

        distance = self.distance

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if coordinates is not UNSET:
            field_dict["coordinates"] = coordinates
        if distance is not UNSET:
            field_dict["distance"] = distance
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        coordinates = cast(list[float], d.pop("coordinates", UNSET))

        distance = d.pop("distance", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: SnapToRoadSuccessType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = SnapToRoadSuccessType(_type_)

        snap_to_road_success = cls(
            coordinates=coordinates,
            distance=distance,
            type_=type_,
        )

        snap_to_road_success.additional_properties = d
        return snap_to_road_success

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

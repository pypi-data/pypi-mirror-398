from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CheckNearbySuccessData")


@_attrs_define
class CheckNearbySuccessData:
    """
    Attributes:
        id (str | Unset):  Example: 68e5f2ab382b2.
        name (str | Unset):  Example: destination.
        radius (str | Unset):  Example: 1000.
        latitude (str | Unset):  Example: 23.76245538673939.
        longitude (str | Unset):  Example: 90.37852866512583.
        user_id (int | Unset):  Example: 1624.
    """

    id: str | Unset = UNSET
    name: str | Unset = UNSET
    radius: str | Unset = UNSET
    latitude: str | Unset = UNSET
    longitude: str | Unset = UNSET
    user_id: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        radius = self.radius

        latitude = self.latitude

        longitude = self.longitude

        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if radius is not UNSET:
            field_dict["radius"] = radius
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if user_id is not UNSET:
            field_dict["user_id"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        radius = d.pop("radius", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        user_id = d.pop("user_id", UNSET)

        check_nearby_success_data = cls(
            id=id,
            name=name,
            radius=radius,
            latitude=latitude,
            longitude=longitude,
            user_id=user_id,
        )

        check_nearby_success_data.additional_properties = d
        return check_nearby_success_data

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

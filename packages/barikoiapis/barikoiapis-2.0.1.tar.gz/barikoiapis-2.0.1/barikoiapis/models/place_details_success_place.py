from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PlaceDetailsSuccessPlace")


@_attrs_define
class PlaceDetailsSuccessPlace:
    """
    Attributes:
        address (str | Unset):
        place_code (str | Unset):
        latitude (str | Unset):
        longitude (str | Unset):
    """

    address: str | Unset = UNSET
    place_code: str | Unset = UNSET
    latitude: str | Unset = UNSET
    longitude: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        place_code = self.place_code

        latitude = self.latitude

        longitude = self.longitude

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if place_code is not UNSET:
            field_dict["place_code"] = place_code
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address", UNSET)

        place_code = d.pop("place_code", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        place_details_success_place = cls(
            address=address,
            place_code=place_code,
            latitude=latitude,
            longitude=longitude,
        )

        place_details_success_place.additional_properties = d
        return place_details_success_place

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

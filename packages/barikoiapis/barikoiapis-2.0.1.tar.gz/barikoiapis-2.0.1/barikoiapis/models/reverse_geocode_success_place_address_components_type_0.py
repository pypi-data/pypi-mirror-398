from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReverseGeocodeSuccessPlaceAddressComponentsType0")


@_attrs_define
class ReverseGeocodeSuccessPlaceAddressComponentsType0:
    """
    Attributes:
        place_name (None | str | Unset):
        house (None | str | Unset):
        road (None | str | Unset):
    """

    place_name: None | str | Unset = UNSET
    house: None | str | Unset = UNSET
    road: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        place_name: None | str | Unset
        if isinstance(self.place_name, Unset):
            place_name = UNSET
        else:
            place_name = self.place_name

        house: None | str | Unset
        if isinstance(self.house, Unset):
            house = UNSET
        else:
            house = self.house

        road: None | str | Unset
        if isinstance(self.road, Unset):
            road = UNSET
        else:
            road = self.road

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if place_name is not UNSET:
            field_dict["place_name"] = place_name
        if house is not UNSET:
            field_dict["house"] = house
        if road is not UNSET:
            field_dict["road"] = road

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_place_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        place_name = _parse_place_name(d.pop("place_name", UNSET))

        def _parse_house(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        house = _parse_house(d.pop("house", UNSET))

        def _parse_road(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        road = _parse_road(d.pop("road", UNSET))

        reverse_geocode_success_place_address_components_type_0 = cls(
            place_name=place_name,
            house=house,
            road=road,
        )

        reverse_geocode_success_place_address_components_type_0.additional_properties = d
        return reverse_geocode_success_place_address_components_type_0

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

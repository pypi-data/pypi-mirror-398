from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReverseGeocodeSuccessPlaceAreaComponentsType0")


@_attrs_define
class ReverseGeocodeSuccessPlaceAreaComponentsType0:
    """
    Attributes:
        area (None | str | Unset):
        sub_area (None | str | Unset):
    """

    area: None | str | Unset = UNSET
    sub_area: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        area: None | str | Unset
        if isinstance(self.area, Unset):
            area = UNSET
        else:
            area = self.area

        sub_area: None | str | Unset
        if isinstance(self.sub_area, Unset):
            sub_area = UNSET
        else:
            sub_area = self.sub_area

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if area is not UNSET:
            field_dict["area"] = area
        if sub_area is not UNSET:
            field_dict["sub_area"] = sub_area

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_area(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        area = _parse_area(d.pop("area", UNSET))

        def _parse_sub_area(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sub_area = _parse_sub_area(d.pop("sub_area", UNSET))

        reverse_geocode_success_place_area_components_type_0 = cls(
            area=area,
            sub_area=sub_area,
        )

        reverse_geocode_success_place_area_components_type_0.additional_properties = d
        return reverse_geocode_success_place_area_components_type_0

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

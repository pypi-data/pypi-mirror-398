from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AutocompleteSuccessPlacesItem")


@_attrs_define
class AutocompleteSuccessPlacesItem:
    """
    Attributes:
        id (int | Unset):  Example: 635085.
        longitude (float | str | Unset):  Example: 90.369999116958.
        latitude (float | str | Unset):  Example: 23.83729875602.
        address (str | Unset):  Example: Mirpur DOHS, Mirpur DOHS.
        address_bn (str | Unset):
        city (str | Unset):  Example: Dhaka.
        city_bn (str | Unset):
        area (str | Unset):
        area_bn (str | Unset):
        post_code (int | str | Unset):  Example: 1216.
        p_type (str | Unset):  Example: Admin.
        u_code (str | Unset):  Example: PFSU6037.
    """

    id: int | Unset = UNSET
    longitude: float | str | Unset = UNSET
    latitude: float | str | Unset = UNSET
    address: str | Unset = UNSET
    address_bn: str | Unset = UNSET
    city: str | Unset = UNSET
    city_bn: str | Unset = UNSET
    area: str | Unset = UNSET
    area_bn: str | Unset = UNSET
    post_code: int | str | Unset = UNSET
    p_type: str | Unset = UNSET
    u_code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        longitude: float | str | Unset
        if isinstance(self.longitude, Unset):
            longitude = UNSET
        else:
            longitude = self.longitude

        latitude: float | str | Unset
        if isinstance(self.latitude, Unset):
            latitude = UNSET
        else:
            latitude = self.latitude

        address = self.address

        address_bn = self.address_bn

        city = self.city

        city_bn = self.city_bn

        area = self.area

        area_bn = self.area_bn

        post_code: int | str | Unset
        if isinstance(self.post_code, Unset):
            post_code = UNSET
        else:
            post_code = self.post_code

        p_type = self.p_type

        u_code = self.u_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if address is not UNSET:
            field_dict["address"] = address
        if address_bn is not UNSET:
            field_dict["address_bn"] = address_bn
        if city is not UNSET:
            field_dict["city"] = city
        if city_bn is not UNSET:
            field_dict["city_bn"] = city_bn
        if area is not UNSET:
            field_dict["area"] = area
        if area_bn is not UNSET:
            field_dict["area_bn"] = area_bn
        if post_code is not UNSET:
            field_dict["postCode"] = post_code
        if p_type is not UNSET:
            field_dict["pType"] = p_type
        if u_code is not UNSET:
            field_dict["uCode"] = u_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_longitude(data: object) -> float | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(float | str | Unset, data)

        longitude = _parse_longitude(d.pop("longitude", UNSET))

        def _parse_latitude(data: object) -> float | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(float | str | Unset, data)

        latitude = _parse_latitude(d.pop("latitude", UNSET))

        address = d.pop("address", UNSET)

        address_bn = d.pop("address_bn", UNSET)

        city = d.pop("city", UNSET)

        city_bn = d.pop("city_bn", UNSET)

        area = d.pop("area", UNSET)

        area_bn = d.pop("area_bn", UNSET)

        def _parse_post_code(data: object) -> int | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(int | str | Unset, data)

        post_code = _parse_post_code(d.pop("postCode", UNSET))

        p_type = d.pop("pType", UNSET)

        u_code = d.pop("uCode", UNSET)

        autocomplete_success_places_item = cls(
            id=id,
            longitude=longitude,
            latitude=latitude,
            address=address,
            address_bn=address_bn,
            city=city,
            city_bn=city_bn,
            area=area,
            area_bn=area_bn,
            post_code=post_code,
            p_type=p_type,
            u_code=u_code,
        )

        autocomplete_success_places_item.additional_properties = d
        return autocomplete_success_places_item

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

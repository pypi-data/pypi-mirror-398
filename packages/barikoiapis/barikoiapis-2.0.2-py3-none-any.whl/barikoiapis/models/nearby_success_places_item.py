from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NearbySuccessPlacesItem")


@_attrs_define
class NearbySuccessPlacesItem:
    """
    Attributes:
        id (int | Unset):
        name (str | Unset):
        distance_in_meters (float | str | Unset):
        longitude (str | Unset):
        latitude (str | Unset):
        p_type (str | Unset):
        address (str | Unset):
        area (str | Unset):
        city (str | Unset):
        post_code (str | Unset):
        sub_type (str | Unset):
        u_code (str | Unset):
    """

    id: int | Unset = UNSET
    name: str | Unset = UNSET
    distance_in_meters: float | str | Unset = UNSET
    longitude: str | Unset = UNSET
    latitude: str | Unset = UNSET
    p_type: str | Unset = UNSET
    address: str | Unset = UNSET
    area: str | Unset = UNSET
    city: str | Unset = UNSET
    post_code: str | Unset = UNSET
    sub_type: str | Unset = UNSET
    u_code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        distance_in_meters: float | str | Unset
        if isinstance(self.distance_in_meters, Unset):
            distance_in_meters = UNSET
        else:
            distance_in_meters = self.distance_in_meters

        longitude = self.longitude

        latitude = self.latitude

        p_type = self.p_type

        address = self.address

        area = self.area

        city = self.city

        post_code = self.post_code

        sub_type = self.sub_type

        u_code = self.u_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if distance_in_meters is not UNSET:
            field_dict["distance_in_meters"] = distance_in_meters
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if p_type is not UNSET:
            field_dict["pType"] = p_type
        if address is not UNSET:
            field_dict["Address"] = address
        if area is not UNSET:
            field_dict["area"] = area
        if city is not UNSET:
            field_dict["city"] = city
        if post_code is not UNSET:
            field_dict["postCode"] = post_code
        if sub_type is not UNSET:
            field_dict["subType"] = sub_type
        if u_code is not UNSET:
            field_dict["uCode"] = u_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        def _parse_distance_in_meters(data: object) -> float | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(float | str | Unset, data)

        distance_in_meters = _parse_distance_in_meters(d.pop("distance_in_meters", UNSET))

        longitude = d.pop("longitude", UNSET)

        latitude = d.pop("latitude", UNSET)

        p_type = d.pop("pType", UNSET)

        address = d.pop("Address", UNSET)

        area = d.pop("area", UNSET)

        city = d.pop("city", UNSET)

        post_code = d.pop("postCode", UNSET)

        sub_type = d.pop("subType", UNSET)

        u_code = d.pop("uCode", UNSET)

        nearby_success_places_item = cls(
            id=id,
            name=name,
            distance_in_meters=distance_in_meters,
            longitude=longitude,
            latitude=latitude,
            p_type=p_type,
            address=address,
            area=area,
            city=city,
            post_code=post_code,
            sub_type=sub_type,
            u_code=u_code,
        )

        nearby_success_places_item.additional_properties = d
        return nearby_success_places_item

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

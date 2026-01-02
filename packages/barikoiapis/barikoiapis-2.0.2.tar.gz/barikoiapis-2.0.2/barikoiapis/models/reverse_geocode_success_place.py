from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.reverse_geocode_success_place_address_components_type_0 import (
        ReverseGeocodeSuccessPlaceAddressComponentsType0,
    )
    from ..models.reverse_geocode_success_place_area_components_type_0 import (
        ReverseGeocodeSuccessPlaceAreaComponentsType0,
    )


T = TypeVar("T", bound="ReverseGeocodeSuccessPlace")


@_attrs_define
class ReverseGeocodeSuccessPlace:
    """
    Attributes:
        id (int | str | Unset):  Example: 6488.
        distance_within_meters (float | Unset):  Example: 3.6856.
        address (str | Unset):  Example: House 8, Road 2, Block C, Section 2, Mirpur, Dhaka.
        area (str | Unset):  Example: Mirpur.
        city (str | Unset):  Example: Dhaka.
        post_code (str | Unset):  Example: 1216.
        address_bn (str | Unset):  Example: বাড়ি ৮, রোড ২, ব্লক সি, সেকশন ২, মিরপুর, ঢাকা.
        area_bn (str | Unset):
        city_bn (str | Unset):
        country (str | Unset):
        division (str | Unset):
        district (str | Unset):
        sub_district (str | Unset):
        pauroshova (None | str | Unset):
        union (None | str | Unset):
        location_type (str | Unset):
        address_components (None | ReverseGeocodeSuccessPlaceAddressComponentsType0 | Unset):
        area_components (None | ReverseGeocodeSuccessPlaceAreaComponentsType0 | Unset):
        thana (str | Unset):
        thana_bn (str | Unset):
    """

    id: int | str | Unset = UNSET
    distance_within_meters: float | Unset = UNSET
    address: str | Unset = UNSET
    area: str | Unset = UNSET
    city: str | Unset = UNSET
    post_code: str | Unset = UNSET
    address_bn: str | Unset = UNSET
    area_bn: str | Unset = UNSET
    city_bn: str | Unset = UNSET
    country: str | Unset = UNSET
    division: str | Unset = UNSET
    district: str | Unset = UNSET
    sub_district: str | Unset = UNSET
    pauroshova: None | str | Unset = UNSET
    union: None | str | Unset = UNSET
    location_type: str | Unset = UNSET
    address_components: None | ReverseGeocodeSuccessPlaceAddressComponentsType0 | Unset = UNSET
    area_components: None | ReverseGeocodeSuccessPlaceAreaComponentsType0 | Unset = UNSET
    thana: str | Unset = UNSET
    thana_bn: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.reverse_geocode_success_place_address_components_type_0 import (
            ReverseGeocodeSuccessPlaceAddressComponentsType0,
        )
        from ..models.reverse_geocode_success_place_area_components_type_0 import (
            ReverseGeocodeSuccessPlaceAreaComponentsType0,
        )

        id: int | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        distance_within_meters = self.distance_within_meters

        address = self.address

        area = self.area

        city = self.city

        post_code = self.post_code

        address_bn = self.address_bn

        area_bn = self.area_bn

        city_bn = self.city_bn

        country = self.country

        division = self.division

        district = self.district

        sub_district = self.sub_district

        pauroshova: None | str | Unset
        if isinstance(self.pauroshova, Unset):
            pauroshova = UNSET
        else:
            pauroshova = self.pauroshova

        union: None | str | Unset
        if isinstance(self.union, Unset):
            union = UNSET
        else:
            union = self.union

        location_type = self.location_type

        address_components: dict[str, Any] | None | Unset
        if isinstance(self.address_components, Unset):
            address_components = UNSET
        elif isinstance(self.address_components, ReverseGeocodeSuccessPlaceAddressComponentsType0):
            address_components = self.address_components.to_dict()
        else:
            address_components = self.address_components

        area_components: dict[str, Any] | None | Unset
        if isinstance(self.area_components, Unset):
            area_components = UNSET
        elif isinstance(self.area_components, ReverseGeocodeSuccessPlaceAreaComponentsType0):
            area_components = self.area_components.to_dict()
        else:
            area_components = self.area_components

        thana = self.thana

        thana_bn = self.thana_bn

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if distance_within_meters is not UNSET:
            field_dict["distance_within_meters"] = distance_within_meters
        if address is not UNSET:
            field_dict["address"] = address
        if area is not UNSET:
            field_dict["area"] = area
        if city is not UNSET:
            field_dict["city"] = city
        if post_code is not UNSET:
            field_dict["postCode"] = post_code
        if address_bn is not UNSET:
            field_dict["address_bn"] = address_bn
        if area_bn is not UNSET:
            field_dict["area_bn"] = area_bn
        if city_bn is not UNSET:
            field_dict["city_bn"] = city_bn
        if country is not UNSET:
            field_dict["country"] = country
        if division is not UNSET:
            field_dict["division"] = division
        if district is not UNSET:
            field_dict["district"] = district
        if sub_district is not UNSET:
            field_dict["sub_district"] = sub_district
        if pauroshova is not UNSET:
            field_dict["pauroshova"] = pauroshova
        if union is not UNSET:
            field_dict["union"] = union
        if location_type is not UNSET:
            field_dict["location_type"] = location_type
        if address_components is not UNSET:
            field_dict["address_components"] = address_components
        if area_components is not UNSET:
            field_dict["area_components"] = area_components
        if thana is not UNSET:
            field_dict["thana"] = thana
        if thana_bn is not UNSET:
            field_dict["thana_bn"] = thana_bn

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reverse_geocode_success_place_address_components_type_0 import (
            ReverseGeocodeSuccessPlaceAddressComponentsType0,
        )
        from ..models.reverse_geocode_success_place_area_components_type_0 import (
            ReverseGeocodeSuccessPlaceAreaComponentsType0,
        )

        d = dict(src_dict)

        def _parse_id(data: object) -> int | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(int | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        distance_within_meters = d.pop("distance_within_meters", UNSET)

        address = d.pop("address", UNSET)

        area = d.pop("area", UNSET)

        city = d.pop("city", UNSET)

        post_code = d.pop("postCode", UNSET)

        address_bn = d.pop("address_bn", UNSET)

        area_bn = d.pop("area_bn", UNSET)

        city_bn = d.pop("city_bn", UNSET)

        country = d.pop("country", UNSET)

        division = d.pop("division", UNSET)

        district = d.pop("district", UNSET)

        sub_district = d.pop("sub_district", UNSET)

        def _parse_pauroshova(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pauroshova = _parse_pauroshova(d.pop("pauroshova", UNSET))

        def _parse_union(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        union = _parse_union(d.pop("union", UNSET))

        location_type = d.pop("location_type", UNSET)

        def _parse_address_components(data: object) -> None | ReverseGeocodeSuccessPlaceAddressComponentsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                address_components_type_0 = ReverseGeocodeSuccessPlaceAddressComponentsType0.from_dict(data)

                return address_components_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ReverseGeocodeSuccessPlaceAddressComponentsType0 | Unset, data)

        address_components = _parse_address_components(d.pop("address_components", UNSET))

        def _parse_area_components(data: object) -> None | ReverseGeocodeSuccessPlaceAreaComponentsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                area_components_type_0 = ReverseGeocodeSuccessPlaceAreaComponentsType0.from_dict(data)

                return area_components_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ReverseGeocodeSuccessPlaceAreaComponentsType0 | Unset, data)

        area_components = _parse_area_components(d.pop("area_components", UNSET))

        thana = d.pop("thana", UNSET)

        thana_bn = d.pop("thana_bn", UNSET)

        reverse_geocode_success_place = cls(
            id=id,
            distance_within_meters=distance_within_meters,
            address=address,
            area=area,
            city=city,
            post_code=post_code,
            address_bn=address_bn,
            area_bn=area_bn,
            city_bn=city_bn,
            country=country,
            division=division,
            district=district,
            sub_district=sub_district,
            pauroshova=pauroshova,
            union=union,
            location_type=location_type,
            address_components=address_components,
            area_components=area_components,
            thana=thana,
            thana_bn=thana_bn,
        )

        reverse_geocode_success_place.additional_properties = d
        return reverse_geocode_success_place

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

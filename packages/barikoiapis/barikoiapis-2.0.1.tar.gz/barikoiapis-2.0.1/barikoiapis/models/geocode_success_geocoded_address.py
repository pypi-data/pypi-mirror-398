from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GeocodeSuccessGeocodedAddress")


@_attrs_define
class GeocodeSuccessGeocodedAddress:
    """
    Attributes:
        id (int | str | Unset):
        Address (str | Unset):
        address (str | Unset):
        address_bn (str | Unset):
        alternate_address (str | Unset):
        area (str | Unset):
        area_bn (str | Unset):
        bounds (None | str | Unset):
        business_name (None | str | Unset):
        city (str | Unset):
        city_bn (str | Unset):
        created_at (str | Unset):
        district (str | Unset):
        geo_location (list[float] | Unset):
        holding_number (None | str | Unset):
        latitude (str | Unset):
        location (str | Unset):
        location_shape (str | Unset):
        longitude (str | Unset):
        match_freq (int | Unset):
        match_fuzzy (int | Unset):
        matching_diff (int | Unset):
        new_address (str | Unset):
        p_type (str | Unset):
        place_code (str | Unset):
        place_name (None | str | Unset):
        popularity_ranking (int | Unset):
        post_code (int | str | Unset):
        postcode (int | str | Unset):
        road_name_number (None | str | Unset):
        score (float | Unset):
        subType (str | Unset):
        sub_area (None | str | Unset):
        sub_district (str | Unset):
        sub_type (str | Unset):
        super_sub_area (None | str | Unset):
        thana (str | Unset):
        type_ (str | Unset):
        u_code (str | Unset):
        union (int | None | str | Unset):
        unions (int | None | str | Unset):
        updated_at (str | Unset):
        user_id (int | Unset):
    """

    id: int | str | Unset = UNSET
    Address: str | Unset = UNSET
    address: str | Unset = UNSET
    address_bn: str | Unset = UNSET
    alternate_address: str | Unset = UNSET
    area: str | Unset = UNSET
    area_bn: str | Unset = UNSET
    bounds: None | str | Unset = UNSET
    business_name: None | str | Unset = UNSET
    city: str | Unset = UNSET
    city_bn: str | Unset = UNSET
    created_at: str | Unset = UNSET
    district: str | Unset = UNSET
    geo_location: list[float] | Unset = UNSET
    holding_number: None | str | Unset = UNSET
    latitude: str | Unset = UNSET
    location: str | Unset = UNSET
    location_shape: str | Unset = UNSET
    longitude: str | Unset = UNSET
    match_freq: int | Unset = UNSET
    match_fuzzy: int | Unset = UNSET
    matching_diff: int | Unset = UNSET
    new_address: str | Unset = UNSET
    p_type: str | Unset = UNSET
    place_code: str | Unset = UNSET
    place_name: None | str | Unset = UNSET
    popularity_ranking: int | Unset = UNSET
    post_code: int | str | Unset = UNSET
    postcode: int | str | Unset = UNSET
    road_name_number: None | str | Unset = UNSET
    score: float | Unset = UNSET
    subType: str | Unset = UNSET
    sub_area: None | str | Unset = UNSET
    sub_district: str | Unset = UNSET
    sub_type: str | Unset = UNSET
    super_sub_area: None | str | Unset = UNSET
    thana: str | Unset = UNSET
    type_: str | Unset = UNSET
    u_code: str | Unset = UNSET
    union: int | None | str | Unset = UNSET
    unions: int | None | str | Unset = UNSET
    updated_at: str | Unset = UNSET
    user_id: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: int | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        Address = self.Address

        address = self.address

        address_bn = self.address_bn

        alternate_address = self.alternate_address

        area = self.area

        area_bn = self.area_bn

        bounds: None | str | Unset
        if isinstance(self.bounds, Unset):
            bounds = UNSET
        else:
            bounds = self.bounds

        business_name: None | str | Unset
        if isinstance(self.business_name, Unset):
            business_name = UNSET
        else:
            business_name = self.business_name

        city = self.city

        city_bn = self.city_bn

        created_at = self.created_at

        district = self.district

        geo_location: list[float] | Unset = UNSET
        if not isinstance(self.geo_location, Unset):
            geo_location = self.geo_location

        holding_number: None | str | Unset
        if isinstance(self.holding_number, Unset):
            holding_number = UNSET
        else:
            holding_number = self.holding_number

        latitude = self.latitude

        location = self.location

        location_shape = self.location_shape

        longitude = self.longitude

        match_freq = self.match_freq

        match_fuzzy = self.match_fuzzy

        matching_diff = self.matching_diff

        new_address = self.new_address

        p_type = self.p_type

        place_code = self.place_code

        place_name: None | str | Unset
        if isinstance(self.place_name, Unset):
            place_name = UNSET
        else:
            place_name = self.place_name

        popularity_ranking = self.popularity_ranking

        post_code: int | str | Unset
        if isinstance(self.post_code, Unset):
            post_code = UNSET
        else:
            post_code = self.post_code

        postcode: int | str | Unset
        if isinstance(self.postcode, Unset):
            postcode = UNSET
        else:
            postcode = self.postcode

        road_name_number: None | str | Unset
        if isinstance(self.road_name_number, Unset):
            road_name_number = UNSET
        else:
            road_name_number = self.road_name_number

        score = self.score

        subType = self.subType

        sub_area: None | str | Unset
        if isinstance(self.sub_area, Unset):
            sub_area = UNSET
        else:
            sub_area = self.sub_area

        sub_district = self.sub_district

        sub_type = self.sub_type

        super_sub_area: None | str | Unset
        if isinstance(self.super_sub_area, Unset):
            super_sub_area = UNSET
        else:
            super_sub_area = self.super_sub_area

        thana = self.thana

        type_ = self.type_

        u_code = self.u_code

        union: int | None | str | Unset
        if isinstance(self.union, Unset):
            union = UNSET
        else:
            union = self.union

        unions: int | None | str | Unset
        if isinstance(self.unions, Unset):
            unions = UNSET
        else:
            unions = self.unions

        updated_at = self.updated_at

        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if Address is not UNSET:
            field_dict["Address"] = Address
        if address is not UNSET:
            field_dict["address"] = address
        if address_bn is not UNSET:
            field_dict["address_bn"] = address_bn
        if alternate_address is not UNSET:
            field_dict["alternate_address"] = alternate_address
        if area is not UNSET:
            field_dict["area"] = area
        if area_bn is not UNSET:
            field_dict["area_bn"] = area_bn
        if bounds is not UNSET:
            field_dict["bounds"] = bounds
        if business_name is not UNSET:
            field_dict["business_name"] = business_name
        if city is not UNSET:
            field_dict["city"] = city
        if city_bn is not UNSET:
            field_dict["city_bn"] = city_bn
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if district is not UNSET:
            field_dict["district"] = district
        if geo_location is not UNSET:
            field_dict["geo_location"] = geo_location
        if holding_number is not UNSET:
            field_dict["holding_number"] = holding_number
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if location is not UNSET:
            field_dict["location"] = location
        if location_shape is not UNSET:
            field_dict["location_shape"] = location_shape
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if match_freq is not UNSET:
            field_dict["match_freq"] = match_freq
        if match_fuzzy is not UNSET:
            field_dict["match_fuzzy"] = match_fuzzy
        if matching_diff is not UNSET:
            field_dict["matching_diff"] = matching_diff
        if new_address is not UNSET:
            field_dict["new_address"] = new_address
        if p_type is not UNSET:
            field_dict["pType"] = p_type
        if place_code is not UNSET:
            field_dict["place_code"] = place_code
        if place_name is not UNSET:
            field_dict["place_name"] = place_name
        if popularity_ranking is not UNSET:
            field_dict["popularity_ranking"] = popularity_ranking
        if post_code is not UNSET:
            field_dict["postCode"] = post_code
        if postcode is not UNSET:
            field_dict["postcode"] = postcode
        if road_name_number is not UNSET:
            field_dict["road_name_number"] = road_name_number
        if score is not UNSET:
            field_dict["score"] = score
        if subType is not UNSET:
            field_dict["subType"] = subType
        if sub_area is not UNSET:
            field_dict["sub_area"] = sub_area
        if sub_district is not UNSET:
            field_dict["sub_district"] = sub_district
        if sub_type is not UNSET:
            field_dict["sub_type"] = sub_type
        if super_sub_area is not UNSET:
            field_dict["super_sub_area"] = super_sub_area
        if thana is not UNSET:
            field_dict["thana"] = thana
        if type_ is not UNSET:
            field_dict["type"] = type_
        if u_code is not UNSET:
            field_dict["uCode"] = u_code
        if union is not UNSET:
            field_dict["union"] = union
        if unions is not UNSET:
            field_dict["unions"] = unions
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if user_id is not UNSET:
            field_dict["user_id"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_id(data: object) -> int | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(int | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        Address = d.pop("Address", UNSET)

        address = d.pop("address", UNSET)

        address_bn = d.pop("address_bn", UNSET)

        alternate_address = d.pop("alternate_address", UNSET)

        area = d.pop("area", UNSET)

        area_bn = d.pop("area_bn", UNSET)

        def _parse_bounds(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bounds = _parse_bounds(d.pop("bounds", UNSET))

        def _parse_business_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        business_name = _parse_business_name(d.pop("business_name", UNSET))

        city = d.pop("city", UNSET)

        city_bn = d.pop("city_bn", UNSET)

        created_at = d.pop("created_at", UNSET)

        district = d.pop("district", UNSET)

        geo_location = cast(list[float], d.pop("geo_location", UNSET))

        def _parse_holding_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        holding_number = _parse_holding_number(d.pop("holding_number", UNSET))

        latitude = d.pop("latitude", UNSET)

        location = d.pop("location", UNSET)

        location_shape = d.pop("location_shape", UNSET)

        longitude = d.pop("longitude", UNSET)

        match_freq = d.pop("match_freq", UNSET)

        match_fuzzy = d.pop("match_fuzzy", UNSET)

        matching_diff = d.pop("matching_diff", UNSET)

        new_address = d.pop("new_address", UNSET)

        p_type = d.pop("pType", UNSET)

        place_code = d.pop("place_code", UNSET)

        def _parse_place_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        place_name = _parse_place_name(d.pop("place_name", UNSET))

        popularity_ranking = d.pop("popularity_ranking", UNSET)

        def _parse_post_code(data: object) -> int | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(int | str | Unset, data)

        post_code = _parse_post_code(d.pop("postCode", UNSET))

        def _parse_postcode(data: object) -> int | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(int | str | Unset, data)

        postcode = _parse_postcode(d.pop("postcode", UNSET))

        def _parse_road_name_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        road_name_number = _parse_road_name_number(d.pop("road_name_number", UNSET))

        score = d.pop("score", UNSET)

        subType = d.pop("subType", UNSET)

        def _parse_sub_area(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sub_area = _parse_sub_area(d.pop("sub_area", UNSET))

        sub_district = d.pop("sub_district", UNSET)

        sub_type = d.pop("sub_type", UNSET)

        def _parse_super_sub_area(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        super_sub_area = _parse_super_sub_area(d.pop("super_sub_area", UNSET))

        thana = d.pop("thana", UNSET)

        type_ = d.pop("type", UNSET)

        u_code = d.pop("uCode", UNSET)

        def _parse_union(data: object) -> int | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | str | Unset, data)

        union = _parse_union(d.pop("union", UNSET))

        def _parse_unions(data: object) -> int | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | str | Unset, data)

        unions = _parse_unions(d.pop("unions", UNSET))

        updated_at = d.pop("updated_at", UNSET)

        user_id = d.pop("user_id", UNSET)

        geocode_success_geocoded_address = cls(
            id=id,
            Address=Address,
            address=address,
            address_bn=address_bn,
            alternate_address=alternate_address,
            area=area,
            area_bn=area_bn,
            bounds=bounds,
            business_name=business_name,
            city=city,
            city_bn=city_bn,
            created_at=created_at,
            district=district,
            geo_location=geo_location,
            holding_number=holding_number,
            latitude=latitude,
            location=location,
            location_shape=location_shape,
            longitude=longitude,
            match_freq=match_freq,
            match_fuzzy=match_fuzzy,
            matching_diff=matching_diff,
            new_address=new_address,
            p_type=p_type,
            place_code=place_code,
            place_name=place_name,
            popularity_ranking=popularity_ranking,
            post_code=post_code,
            postcode=postcode,
            road_name_number=road_name_number,
            score=score,
            subType=subType,
            sub_area=sub_area,
            sub_district=sub_district,
            sub_type=sub_type,
            super_sub_area=super_sub_area,
            thana=thana,
            type_=type_,
            u_code=u_code,
            union=union,
            unions=unions,
            updated_at=updated_at,
            user_id=user_id,
        )

        geocode_success_geocoded_address.additional_properties = d
        return geocode_success_geocoded_address

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

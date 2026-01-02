from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.reverse_geocode_success_place import ReverseGeocodeSuccessPlace


T = TypeVar("T", bound="ReverseGeocodeSuccess")


@_attrs_define
class ReverseGeocodeSuccess:
    """
    Attributes:
        place (ReverseGeocodeSuccessPlace | Unset):
        status (int | Unset):  Example: 200.
    """

    place: ReverseGeocodeSuccessPlace | Unset = UNSET
    status: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        place: dict[str, Any] | Unset = UNSET
        if not isinstance(self.place, Unset):
            place = self.place.to_dict()

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if place is not UNSET:
            field_dict["place"] = place
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reverse_geocode_success_place import ReverseGeocodeSuccessPlace

        d = dict(src_dict)
        _place = d.pop("place", UNSET)
        place: ReverseGeocodeSuccessPlace | Unset
        if isinstance(_place, Unset):
            place = UNSET
        else:
            place = ReverseGeocodeSuccessPlace.from_dict(_place)

        status = d.pop("status", UNSET)

        reverse_geocode_success = cls(
            place=place,
            status=status,
        )

        reverse_geocode_success.additional_properties = d
        return reverse_geocode_success

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

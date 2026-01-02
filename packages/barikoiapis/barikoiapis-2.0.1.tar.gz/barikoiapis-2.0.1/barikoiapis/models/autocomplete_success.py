from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.autocomplete_success_places_item import AutocompleteSuccessPlacesItem


T = TypeVar("T", bound="AutocompleteSuccess")


@_attrs_define
class AutocompleteSuccess:
    """
    Attributes:
        places (list[AutocompleteSuccessPlacesItem] | Unset):
        status (int | Unset):  Example: 200.
    """

    places: list[AutocompleteSuccessPlacesItem] | Unset = UNSET
    status: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        places: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.places, Unset):
            places = []
            for places_item_data in self.places:
                places_item = places_item_data.to_dict()
                places.append(places_item)

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if places is not UNSET:
            field_dict["places"] = places
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.autocomplete_success_places_item import AutocompleteSuccessPlacesItem

        d = dict(src_dict)
        _places = d.pop("places", UNSET)
        places: list[AutocompleteSuccessPlacesItem] | Unset = UNSET
        if _places is not UNSET:
            places = []
            for places_item_data in _places:
                places_item = AutocompleteSuccessPlacesItem.from_dict(places_item_data)

                places.append(places_item)

        status = d.pop("status", UNSET)

        autocomplete_success = cls(
            places=places,
            status=status,
        )

        autocomplete_success.additional_properties = d
        return autocomplete_success

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

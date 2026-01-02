from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.place_details_success_place import PlaceDetailsSuccessPlace


T = TypeVar("T", bound="PlaceDetailsSuccess")


@_attrs_define
class PlaceDetailsSuccess:
    """
    Attributes:
        place (PlaceDetailsSuccessPlace | Unset):
        session_id (UUID | Unset):
        status (int | Unset):  Example: 200.
    """

    place: PlaceDetailsSuccessPlace | Unset = UNSET
    session_id: UUID | Unset = UNSET
    status: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        place: dict[str, Any] | Unset = UNSET
        if not isinstance(self.place, Unset):
            place = self.place.to_dict()

        session_id: str | Unset = UNSET
        if not isinstance(self.session_id, Unset):
            session_id = str(self.session_id)

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if place is not UNSET:
            field_dict["place"] = place
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.place_details_success_place import PlaceDetailsSuccessPlace

        d = dict(src_dict)
        _place = d.pop("place", UNSET)
        place: PlaceDetailsSuccessPlace | Unset
        if isinstance(_place, Unset):
            place = UNSET
        else:
            place = PlaceDetailsSuccessPlace.from_dict(_place)

        _session_id = d.pop("session_id", UNSET)
        session_id: UUID | Unset
        if isinstance(_session_id, Unset):
            session_id = UNSET
        else:
            session_id = UUID(_session_id)

        status = d.pop("status", UNSET)

        place_details_success = cls(
            place=place,
            session_id=session_id,
            status=status,
        )

        place_details_success.additional_properties = d
        return place_details_success

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

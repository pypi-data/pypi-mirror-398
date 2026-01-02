from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.geocode_body_bangla import GeocodeBodyBangla
from ..models.geocode_body_district import GeocodeBodyDistrict
from ..models.geocode_body_thana import GeocodeBodyThana
from ..types import UNSET, Unset

T = TypeVar("T", bound="GeocodeBody")


@_attrs_define
class GeocodeBody:
    """
    Attributes:
        q (str): Address to geocode
        thana (GeocodeBodyThana | Unset):
        district (GeocodeBodyDistrict | Unset):
        bangla (GeocodeBodyBangla | Unset):
    """

    q: str
    thana: GeocodeBodyThana | Unset = UNSET
    district: GeocodeBodyDistrict | Unset = UNSET
    bangla: GeocodeBodyBangla | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        q = self.q

        thana: str | Unset = UNSET
        if not isinstance(self.thana, Unset):
            thana = self.thana.value

        district: str | Unset = UNSET
        if not isinstance(self.district, Unset):
            district = self.district.value

        bangla: str | Unset = UNSET
        if not isinstance(self.bangla, Unset):
            bangla = self.bangla.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "q": q,
            }
        )
        if thana is not UNSET:
            field_dict["thana"] = thana
        if district is not UNSET:
            field_dict["district"] = district
        if bangla is not UNSET:
            field_dict["bangla"] = bangla

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        q = d.pop("q")

        _thana = d.pop("thana", UNSET)
        thana: GeocodeBodyThana | Unset
        if isinstance(_thana, Unset):
            thana = UNSET
        else:
            thana = GeocodeBodyThana(_thana)

        _district = d.pop("district", UNSET)
        district: GeocodeBodyDistrict | Unset
        if isinstance(_district, Unset):
            district = UNSET
        else:
            district = GeocodeBodyDistrict(_district)

        _bangla = d.pop("bangla", UNSET)
        bangla: GeocodeBodyBangla | Unset
        if isinstance(_bangla, Unset):
            bangla = UNSET
        else:
            bangla = GeocodeBodyBangla(_bangla)

        geocode_body = cls(
            q=q,
            thana=thana,
            district=district,
            bangla=bangla,
        )

        geocode_body.additional_properties = d
        return geocode_body

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

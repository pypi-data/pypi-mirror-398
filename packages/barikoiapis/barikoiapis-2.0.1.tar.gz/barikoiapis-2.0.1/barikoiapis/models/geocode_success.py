from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.geocode_success_address_status import GeocodeSuccessAddressStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.geocode_success_geocoded_address import GeocodeSuccessGeocodedAddress


T = TypeVar("T", bound="GeocodeSuccess")


@_attrs_define
class GeocodeSuccess:
    """
    Attributes:
        given_address (str | Unset):  Example: shawrapara.
        fixed_address (str | Unset):  Example: shewrapara, mirpur.
        bangla_address (str | Unset):
        address_status (GeocodeSuccessAddressStatus | Unset):  Example: incomplete.
        geocoded_address (GeocodeSuccessGeocodedAddress | Unset):
        confidence_score_percentage (int | Unset):  Example: 70.
        status (int | Unset):  Example: 200.
    """

    given_address: str | Unset = UNSET
    fixed_address: str | Unset = UNSET
    bangla_address: str | Unset = UNSET
    address_status: GeocodeSuccessAddressStatus | Unset = UNSET
    geocoded_address: GeocodeSuccessGeocodedAddress | Unset = UNSET
    confidence_score_percentage: int | Unset = UNSET
    status: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        given_address = self.given_address

        fixed_address = self.fixed_address

        bangla_address = self.bangla_address

        address_status: str | Unset = UNSET
        if not isinstance(self.address_status, Unset):
            address_status = self.address_status.value

        geocoded_address: dict[str, Any] | Unset = UNSET
        if not isinstance(self.geocoded_address, Unset):
            geocoded_address = self.geocoded_address.to_dict()

        confidence_score_percentage = self.confidence_score_percentage

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if given_address is not UNSET:
            field_dict["given_address"] = given_address
        if fixed_address is not UNSET:
            field_dict["fixed_address"] = fixed_address
        if bangla_address is not UNSET:
            field_dict["bangla_address"] = bangla_address
        if address_status is not UNSET:
            field_dict["address_status"] = address_status
        if geocoded_address is not UNSET:
            field_dict["geocoded_address"] = geocoded_address
        if confidence_score_percentage is not UNSET:
            field_dict["confidence_score_percentage"] = confidence_score_percentage
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.geocode_success_geocoded_address import GeocodeSuccessGeocodedAddress

        d = dict(src_dict)
        given_address = d.pop("given_address", UNSET)

        fixed_address = d.pop("fixed_address", UNSET)

        bangla_address = d.pop("bangla_address", UNSET)

        _address_status = d.pop("address_status", UNSET)
        address_status: GeocodeSuccessAddressStatus | Unset
        if isinstance(_address_status, Unset):
            address_status = UNSET
        else:
            address_status = GeocodeSuccessAddressStatus(_address_status)

        _geocoded_address = d.pop("geocoded_address", UNSET)
        geocoded_address: GeocodeSuccessGeocodedAddress | Unset
        if isinstance(_geocoded_address, Unset):
            geocoded_address = UNSET
        else:
            geocoded_address = GeocodeSuccessGeocodedAddress.from_dict(_geocoded_address)

        confidence_score_percentage = d.pop("confidence_score_percentage", UNSET)

        status = d.pop("status", UNSET)

        geocode_success = cls(
            given_address=given_address,
            fixed_address=fixed_address,
            bangla_address=bangla_address,
            address_status=address_status,
            geocoded_address=geocoded_address,
            confidence_score_percentage=confidence_score_percentage,
            status=status,
        )

        geocode_success.additional_properties = d
        return geocode_success

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

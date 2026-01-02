from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.calculate_route_body_data_destination import CalculateRouteBodyDataDestination
    from ..models.calculate_route_body_data_start import CalculateRouteBodyDataStart


T = TypeVar("T", bound="CalculateRouteBodyData")


@_attrs_define
class CalculateRouteBodyData:
    """
    Attributes:
        start (CalculateRouteBodyDataStart):
        destination (CalculateRouteBodyDataDestination):
    """

    start: CalculateRouteBodyDataStart
    destination: CalculateRouteBodyDataDestination
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start = self.start.to_dict()

        destination = self.destination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "start": start,
                "destination": destination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.calculate_route_body_data_destination import CalculateRouteBodyDataDestination
        from ..models.calculate_route_body_data_start import CalculateRouteBodyDataStart

        d = dict(src_dict)
        start = CalculateRouteBodyDataStart.from_dict(d.pop("start"))

        destination = CalculateRouteBodyDataDestination.from_dict(d.pop("destination"))

        calculate_route_body_data = cls(
            start=start,
            destination=destination,
        )

        calculate_route_body_data.additional_properties = d
        return calculate_route_body_data

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

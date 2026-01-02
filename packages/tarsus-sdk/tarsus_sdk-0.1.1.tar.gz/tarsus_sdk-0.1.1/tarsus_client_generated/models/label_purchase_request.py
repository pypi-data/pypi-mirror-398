from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="LabelPurchaseRequest")


@_attrs_define
class LabelPurchaseRequest:
    """Request model for purchasing shipping labels.

    Attributes:
        shipment_id (str):
        rate_id (str):
    """

    shipment_id: str
    rate_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment_id = self.shipment_id

        rate_id = self.rate_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shipment_id": shipment_id,
                "rate_id": rate_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        shipment_id = d.pop("shipment_id")

        rate_id = d.pop("rate_id")

        label_purchase_request = cls(
            shipment_id=shipment_id,
            rate_id=rate_id,
        )

        label_purchase_request.additional_properties = d
        return label_purchase_request

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

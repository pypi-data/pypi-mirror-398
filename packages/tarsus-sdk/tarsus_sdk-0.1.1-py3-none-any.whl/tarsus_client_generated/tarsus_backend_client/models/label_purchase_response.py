from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.label_purchase_response_postage_label import LabelPurchaseResponsePostageLabel


T = TypeVar("T", bound="LabelPurchaseResponse")


@_attrs_define
class LabelPurchaseResponse:
    """Response model for label purchase.

    Attributes:
        tracking_code (str):
        label_url (str):
        postage_label (LabelPurchaseResponsePostageLabel):
        shipment_id (str):
    """

    tracking_code: str
    label_url: str
    postage_label: LabelPurchaseResponsePostageLabel
    shipment_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tracking_code = self.tracking_code

        label_url = self.label_url

        postage_label = self.postage_label.to_dict()

        shipment_id = self.shipment_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tracking_code": tracking_code,
                "label_url": label_url,
                "postage_label": postage_label,
                "shipment_id": shipment_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.label_purchase_response_postage_label import LabelPurchaseResponsePostageLabel

        d = dict(src_dict)
        tracking_code = d.pop("tracking_code")

        label_url = d.pop("label_url")

        postage_label = LabelPurchaseResponsePostageLabel.from_dict(d.pop("postage_label"))

        shipment_id = d.pop("shipment_id")

        label_purchase_response = cls(
            tracking_code=tracking_code,
            label_url=label_url,
            postage_label=postage_label,
            shipment_id=shipment_id,
        )

        label_purchase_response.additional_properties = d
        return label_purchase_response

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

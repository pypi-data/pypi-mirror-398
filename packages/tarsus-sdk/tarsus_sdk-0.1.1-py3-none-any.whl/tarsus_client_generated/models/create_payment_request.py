from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CreatePaymentRequest")


@_attrs_define
class CreatePaymentRequest:
    """
    Attributes:
        amount_cents (int):
        source_id (str):
        order_id (str):
    """

    amount_cents: int
    source_id: str
    order_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        amount_cents = self.amount_cents

        source_id = self.source_id

        order_id = self.order_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "amount_cents": amount_cents,
                "source_id": source_id,
                "order_id": order_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount_cents = d.pop("amount_cents")

        source_id = d.pop("source_id")

        order_id = d.pop("order_id")

        create_payment_request = cls(
            amount_cents=amount_cents,
            source_id=source_id,
            order_id=order_id,
        )

        create_payment_request.additional_properties = d
        return create_payment_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.payment_method_info_billing_details_type_0 import PaymentMethodInfoBillingDetailsType0
    from ..models.payment_method_info_card_type_0 import PaymentMethodInfoCardType0


T = TypeVar("T", bound="PaymentMethodInfo")


@_attrs_define
class PaymentMethodInfo:
    """Payment method information model.

    Attributes:
        id (str):
        type_ (str):
        card (None | PaymentMethodInfoCardType0 | Unset):
        billing_details (None | PaymentMethodInfoBillingDetailsType0 | Unset):
    """

    id: str
    type_: str
    card: None | PaymentMethodInfoCardType0 | Unset = UNSET
    billing_details: None | PaymentMethodInfoBillingDetailsType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.payment_method_info_billing_details_type_0 import PaymentMethodInfoBillingDetailsType0
        from ..models.payment_method_info_card_type_0 import PaymentMethodInfoCardType0

        id = self.id

        type_ = self.type_

        card: dict[str, Any] | None | Unset
        if isinstance(self.card, Unset):
            card = UNSET
        elif isinstance(self.card, PaymentMethodInfoCardType0):
            card = self.card.to_dict()
        else:
            card = self.card

        billing_details: dict[str, Any] | None | Unset
        if isinstance(self.billing_details, Unset):
            billing_details = UNSET
        elif isinstance(self.billing_details, PaymentMethodInfoBillingDetailsType0):
            billing_details = self.billing_details.to_dict()
        else:
            billing_details = self.billing_details

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
            }
        )
        if card is not UNSET:
            field_dict["card"] = card
        if billing_details is not UNSET:
            field_dict["billing_details"] = billing_details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.payment_method_info_billing_details_type_0 import PaymentMethodInfoBillingDetailsType0
        from ..models.payment_method_info_card_type_0 import PaymentMethodInfoCardType0

        d = dict(src_dict)
        id = d.pop("id")

        type_ = d.pop("type")

        def _parse_card(data: object) -> None | PaymentMethodInfoCardType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                card_type_0 = PaymentMethodInfoCardType0.from_dict(data)

                return card_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PaymentMethodInfoCardType0 | Unset, data)

        card = _parse_card(d.pop("card", UNSET))

        def _parse_billing_details(data: object) -> None | PaymentMethodInfoBillingDetailsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                billing_details_type_0 = PaymentMethodInfoBillingDetailsType0.from_dict(data)

                return billing_details_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PaymentMethodInfoBillingDetailsType0 | Unset, data)

        billing_details = _parse_billing_details(d.pop("billing_details", UNSET))

        payment_method_info = cls(
            id=id,
            type_=type_,
            card=card,
            billing_details=billing_details,
        )

        payment_method_info.additional_properties = d
        return payment_method_info

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

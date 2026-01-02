from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WalletPaymentIntentResponse")


@_attrs_define
class WalletPaymentIntentResponse:
    """Response containing PaymentIntent client_secret for frontend.

    Attributes:
        client_secret (str): Client secret for PaymentIntent
        payment_intent_id (str): PaymentIntent ID
        publishable_key (None | str | Unset): Stripe publishable key for frontend
    """

    client_secret: str
    payment_intent_id: str
    publishable_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client_secret = self.client_secret

        payment_intent_id = self.payment_intent_id

        publishable_key: None | str | Unset
        if isinstance(self.publishable_key, Unset):
            publishable_key = UNSET
        else:
            publishable_key = self.publishable_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "client_secret": client_secret,
                "payment_intent_id": payment_intent_id,
            }
        )
        if publishable_key is not UNSET:
            field_dict["publishable_key"] = publishable_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client_secret = d.pop("client_secret")

        payment_intent_id = d.pop("payment_intent_id")

        def _parse_publishable_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        publishable_key = _parse_publishable_key(d.pop("publishable_key", UNSET))

        wallet_payment_intent_response = cls(
            client_secret=client_secret,
            payment_intent_id=payment_intent_id,
            publishable_key=publishable_key,
        )

        wallet_payment_intent_response.additional_properties = d
        return wallet_payment_intent_response

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

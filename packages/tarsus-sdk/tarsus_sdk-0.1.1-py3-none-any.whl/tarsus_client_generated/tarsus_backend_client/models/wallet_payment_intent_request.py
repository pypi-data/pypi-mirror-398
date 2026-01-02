from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.wallet_payment_intent_request_metadata_type_0 import WalletPaymentIntentRequestMetadataType0


T = TypeVar("T", bound="WalletPaymentIntentRequest")


@_attrs_define
class WalletPaymentIntentRequest:
    """Request to create PaymentIntent for wallet payment (Google Pay/Apple Pay).

    Attributes:
        amount_cents (int): Amount in cents
        currency (str | Unset): Currency code (default: usd) Default: 'usd'.
        description (None | str | Unset): Optional payment description
        metadata (None | Unset | WalletPaymentIntentRequestMetadataType0): Optional metadata to attach to payment
        customer_id (None | str | Unset): Optional Stripe customer ID
    """

    amount_cents: int
    currency: str | Unset = "usd"
    description: None | str | Unset = UNSET
    metadata: None | Unset | WalletPaymentIntentRequestMetadataType0 = UNSET
    customer_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.wallet_payment_intent_request_metadata_type_0 import WalletPaymentIntentRequestMetadataType0

        amount_cents = self.amount_cents

        currency = self.currency

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, WalletPaymentIntentRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        customer_id: None | str | Unset
        if isinstance(self.customer_id, Unset):
            customer_id = UNSET
        else:
            customer_id = self.customer_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "amount_cents": amount_cents,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.wallet_payment_intent_request_metadata_type_0 import WalletPaymentIntentRequestMetadataType0

        d = dict(src_dict)
        amount_cents = d.pop("amount_cents")

        currency = d.pop("currency", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_metadata(data: object) -> None | Unset | WalletPaymentIntentRequestMetadataType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = WalletPaymentIntentRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WalletPaymentIntentRequestMetadataType0, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_customer_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_id = _parse_customer_id(d.pop("customer_id", UNSET))

        wallet_payment_intent_request = cls(
            amount_cents=amount_cents,
            currency=currency,
            description=description,
            metadata=metadata,
            customer_id=customer_id,
        )

        wallet_payment_intent_request.additional_properties = d
        return wallet_payment_intent_request

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

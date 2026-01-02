from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_subscription_with_wallet_request_metadata_type_0 import (
        CreateSubscriptionWithWalletRequestMetadataType0,
    )


T = TypeVar("T", bound="CreateSubscriptionWithWalletRequest")


@_attrs_define
class CreateSubscriptionWithWalletRequest:
    """Request to create subscription with wallet payment method.

    Attributes:
        price_id (str): Stripe Price ID for subscription tier
        payment_method_id (str): Stripe PaymentMethod ID from wallet
        metadata (CreateSubscriptionWithWalletRequestMetadataType0 | None | Unset): Optional metadata to attach to
            subscription
        customer_id (None | str | Unset): Optional Stripe customer ID (will be created if not provided)
    """

    price_id: str
    payment_method_id: str
    metadata: CreateSubscriptionWithWalletRequestMetadataType0 | None | Unset = UNSET
    customer_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_subscription_with_wallet_request_metadata_type_0 import (
            CreateSubscriptionWithWalletRequestMetadataType0,
        )

        price_id = self.price_id

        payment_method_id = self.payment_method_id

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, CreateSubscriptionWithWalletRequestMetadataType0):
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
                "price_id": price_id,
                "payment_method_id": payment_method_id,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_subscription_with_wallet_request_metadata_type_0 import (
            CreateSubscriptionWithWalletRequestMetadataType0,
        )

        d = dict(src_dict)
        price_id = d.pop("price_id")

        payment_method_id = d.pop("payment_method_id")

        def _parse_metadata(
            data: object,
        ) -> CreateSubscriptionWithWalletRequestMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = CreateSubscriptionWithWalletRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateSubscriptionWithWalletRequestMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_customer_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        customer_id = _parse_customer_id(d.pop("customer_id", UNSET))

        create_subscription_with_wallet_request = cls(
            price_id=price_id,
            payment_method_id=payment_method_id,
            metadata=metadata,
            customer_id=customer_id,
        )

        create_subscription_with_wallet_request.additional_properties = d
        return create_subscription_with_wallet_request

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

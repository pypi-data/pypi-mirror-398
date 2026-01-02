from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.checkout_item_request import CheckoutItemRequest
    from ..models.checkout_request_shipping_address_type_0 import (
        CheckoutRequestShippingAddressType0,
    )


T = TypeVar("T", bound="CheckoutRequest")


@_attrs_define
class CheckoutRequest:
    """Checkout request from frontend.

    Attributes:
        items (list[CheckoutItemRequest]):
        success_url (None | str | Unset):
        cancel_url (None | str | Unset):
        shipping_address (CheckoutRequestShippingAddressType0 | None | Unset):
    """

    items: list[CheckoutItemRequest]
    success_url: None | str | Unset = UNSET
    cancel_url: None | str | Unset = UNSET
    shipping_address: CheckoutRequestShippingAddressType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.checkout_request_shipping_address_type_0 import (
            CheckoutRequestShippingAddressType0,
        )

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        success_url: None | str | Unset
        if isinstance(self.success_url, Unset):
            success_url = UNSET
        else:
            success_url = self.success_url

        cancel_url: None | str | Unset
        if isinstance(self.cancel_url, Unset):
            cancel_url = UNSET
        else:
            cancel_url = self.cancel_url

        shipping_address: dict[str, Any] | None | Unset
        if isinstance(self.shipping_address, Unset):
            shipping_address = UNSET
        elif isinstance(self.shipping_address, CheckoutRequestShippingAddressType0):
            shipping_address = self.shipping_address.to_dict()
        else:
            shipping_address = self.shipping_address

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
            }
        )
        if success_url is not UNSET:
            field_dict["success_url"] = success_url
        if cancel_url is not UNSET:
            field_dict["cancel_url"] = cancel_url
        if shipping_address is not UNSET:
            field_dict["shipping_address"] = shipping_address

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.checkout_item_request import CheckoutItemRequest
        from ..models.checkout_request_shipping_address_type_0 import (
            CheckoutRequestShippingAddressType0,
        )

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = CheckoutItemRequest.from_dict(items_item_data)

            items.append(items_item)

        def _parse_success_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        success_url = _parse_success_url(d.pop("success_url", UNSET))

        def _parse_cancel_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cancel_url = _parse_cancel_url(d.pop("cancel_url", UNSET))

        def _parse_shipping_address(
            data: object,
        ) -> CheckoutRequestShippingAddressType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                shipping_address_type_0 = CheckoutRequestShippingAddressType0.from_dict(data)

                return shipping_address_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CheckoutRequestShippingAddressType0 | None | Unset, data)

        shipping_address = _parse_shipping_address(d.pop("shipping_address", UNSET))

        checkout_request = cls(
            items=items,
            success_url=success_url,
            cancel_url=cancel_url,
            shipping_address=shipping_address,
        )

        checkout_request.additional_properties = d
        return checkout_request

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

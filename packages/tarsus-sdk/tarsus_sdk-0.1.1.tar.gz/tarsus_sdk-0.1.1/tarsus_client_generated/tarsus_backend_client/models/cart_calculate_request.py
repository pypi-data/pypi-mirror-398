from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cart_calculate_request_cart_items_item import CartCalculateRequestCartItemsItem


T = TypeVar("T", bound="CartCalculateRequest")


@_attrs_define
class CartCalculateRequest:
    """
    Attributes:
        cart_items (list[CartCalculateRequestCartItemsItem]):
        cart_total (float):
        coupon_code (None | str | Unset):
    """

    cart_items: list[CartCalculateRequestCartItemsItem]
    cart_total: float
    coupon_code: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cart_items = []
        for cart_items_item_data in self.cart_items:
            cart_items_item = cart_items_item_data.to_dict()
            cart_items.append(cart_items_item)

        cart_total = self.cart_total

        coupon_code: None | str | Unset
        if isinstance(self.coupon_code, Unset):
            coupon_code = UNSET
        else:
            coupon_code = self.coupon_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cart_items": cart_items,
                "cart_total": cart_total,
            }
        )
        if coupon_code is not UNSET:
            field_dict["coupon_code"] = coupon_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cart_calculate_request_cart_items_item import CartCalculateRequestCartItemsItem

        d = dict(src_dict)
        cart_items = []
        _cart_items = d.pop("cart_items")
        for cart_items_item_data in _cart_items:
            cart_items_item = CartCalculateRequestCartItemsItem.from_dict(cart_items_item_data)

            cart_items.append(cart_items_item)

        cart_total = d.pop("cart_total")

        def _parse_coupon_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        coupon_code = _parse_coupon_code(d.pop("coupon_code", UNSET))

        cart_calculate_request = cls(
            cart_items=cart_items,
            cart_total=cart_total,
            coupon_code=coupon_code,
        )

        cart_calculate_request.additional_properties = d
        return cart_calculate_request

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

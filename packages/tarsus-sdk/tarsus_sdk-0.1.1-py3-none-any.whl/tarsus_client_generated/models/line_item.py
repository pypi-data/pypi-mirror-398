from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.line_item_base_price_money_type_0 import LineItemBasePriceMoneyType0


T = TypeVar("T", bound="LineItem")


@_attrs_define
class LineItem:
    """Represents a single item in a Stripe payment.
    Flexible to accept various frontend formats.

        Attributes:
            name (str):
            quantity (int | str):
            item_type (str | Unset):  Default: 'ITEM'.
            base_price_money (LineItemBasePriceMoneyType0 | None | Unset):
            price (float | int | None | Unset):
            amount (float | int | None | Unset):
            currency (None | str | Unset):  Default: 'USD'.
    """

    name: str
    quantity: int | str
    item_type: str | Unset = "ITEM"
    base_price_money: LineItemBasePriceMoneyType0 | None | Unset = UNSET
    price: float | int | None | Unset = UNSET
    amount: float | int | None | Unset = UNSET
    currency: None | str | Unset = "USD"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.line_item_base_price_money_type_0 import (
            LineItemBasePriceMoneyType0,
        )

        name = self.name

        quantity: int | str
        quantity = self.quantity

        item_type = self.item_type

        base_price_money: dict[str, Any] | None | Unset
        if isinstance(self.base_price_money, Unset):
            base_price_money = UNSET
        elif isinstance(self.base_price_money, LineItemBasePriceMoneyType0):
            base_price_money = self.base_price_money.to_dict()
        else:
            base_price_money = self.base_price_money

        price: float | int | None | Unset
        if isinstance(self.price, Unset):
            price = UNSET
        else:
            price = self.price

        amount: float | int | None | Unset
        if isinstance(self.amount, Unset):
            amount = UNSET
        else:
            amount = self.amount

        currency: None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "quantity": quantity,
            }
        )
        if item_type is not UNSET:
            field_dict["item_type"] = item_type
        if base_price_money is not UNSET:
            field_dict["base_price_money"] = base_price_money
        if price is not UNSET:
            field_dict["price"] = price
        if amount is not UNSET:
            field_dict["amount"] = amount
        if currency is not UNSET:
            field_dict["currency"] = currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.line_item_base_price_money_type_0 import (
            LineItemBasePriceMoneyType0,
        )

        d = dict(src_dict)
        name = d.pop("name")

        def _parse_quantity(data: object) -> int | str:
            return cast(int | str, data)

        quantity = _parse_quantity(d.pop("quantity"))

        item_type = d.pop("item_type", UNSET)

        def _parse_base_price_money(
            data: object,
        ) -> LineItemBasePriceMoneyType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                base_price_money_type_0 = LineItemBasePriceMoneyType0.from_dict(data)

                return base_price_money_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(LineItemBasePriceMoneyType0 | None | Unset, data)

        base_price_money = _parse_base_price_money(d.pop("base_price_money", UNSET))

        def _parse_price(data: object) -> float | int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | int | None | Unset, data)

        price = _parse_price(d.pop("price", UNSET))

        def _parse_amount(data: object) -> float | int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | int | None | Unset, data)

        amount = _parse_amount(d.pop("amount", UNSET))

        def _parse_currency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        line_item = cls(
            name=name,
            quantity=quantity,
            item_type=item_type,
            base_price_money=base_price_money,
            price=price,
            amount=amount,
            currency=currency,
        )

        line_item.additional_properties = d
        return line_item

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

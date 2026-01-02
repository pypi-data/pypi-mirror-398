from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_public_role import UserPublicRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.address_model import AddressModel
    from ..models.order_info import OrderInfo


T = TypeVar("T", bound="UserPublic")


@_attrs_define
class UserPublic:
    """
    Attributes:
        id (None | str):
        email (str):
        first_name (None | str):
        last_name (None | str):
        address (AddressModel | None):
        phone_number (None | str):
        card_last4 (None | str):
        role (UserPublicRole):
        created_at (datetime.datetime):
        orders (list[OrderInfo] | Unset):
    """

    id: None | str
    email: str
    first_name: None | str
    last_name: None | str
    address: AddressModel | None
    phone_number: None | str
    card_last4: None | str
    role: UserPublicRole
    created_at: datetime.datetime
    orders: list[OrderInfo] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.address_model import AddressModel

        id: None | str
        id = self.id

        email = self.email

        first_name: None | str
        first_name = self.first_name

        last_name: None | str
        last_name = self.last_name

        address: dict[str, Any] | None
        if isinstance(self.address, AddressModel):
            address = self.address.to_dict()
        else:
            address = self.address

        phone_number: None | str
        phone_number = self.phone_number

        card_last4: None | str
        card_last4 = self.card_last4

        role = self.role.value

        created_at = self.created_at.isoformat()

        orders: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.orders, Unset):
            orders = []
            for orders_item_data in self.orders:
                orders_item = orders_item_data.to_dict()
                orders.append(orders_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "phone_number": phone_number,
                "card_last4": card_last4,
                "role": role,
                "created_at": created_at,
            }
        )
        if orders is not UNSET:
            field_dict["orders"] = orders

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.address_model import AddressModel
        from ..models.order_info import OrderInfo

        d = dict(src_dict)

        def _parse_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        id = _parse_id(d.pop("id"))

        email = d.pop("email")

        def _parse_first_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        first_name = _parse_first_name(d.pop("first_name"))

        def _parse_last_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_name = _parse_last_name(d.pop("last_name"))

        def _parse_address(data: object) -> AddressModel | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                address_type_0 = AddressModel.from_dict(data)

                return address_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AddressModel | None, data)

        address = _parse_address(d.pop("address"))

        def _parse_phone_number(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        phone_number = _parse_phone_number(d.pop("phone_number"))

        def _parse_card_last4(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        card_last4 = _parse_card_last4(d.pop("card_last4"))

        role = UserPublicRole(d.pop("role"))

        created_at = isoparse(d.pop("created_at"))

        _orders = d.pop("orders", UNSET)
        orders: list[OrderInfo] | Unset = UNSET
        if _orders is not UNSET:
            orders = []
            for orders_item_data in _orders:
                orders_item = OrderInfo.from_dict(orders_item_data)

                orders.append(orders_item)

        user_public = cls(
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            address=address,
            phone_number=phone_number,
            card_last4=card_last4,
            role=role,
            created_at=created_at,
            orders=orders,
        )

        user_public.additional_properties = d
        return user_public

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

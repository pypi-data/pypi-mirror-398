from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_create_role import UserCreateRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.address_model import AddressModel


T = TypeVar("T", bound="UserCreate")


@_attrs_define
class UserCreate:
    """
    Attributes:
        email (str):
        password (None | str | Unset):
        first_name (None | str | Unset):
        last_name (None | str | Unset):
        address (AddressModel | None | Unset):
        phone_number (None | str | Unset):
        card_last4 (None | str | Unset):
        role (UserCreateRole | Unset):  Default: UserCreateRole.CUSTOMER.
    """

    email: str
    password: None | str | Unset = UNSET
    first_name: None | str | Unset = UNSET
    last_name: None | str | Unset = UNSET
    address: AddressModel | None | Unset = UNSET
    phone_number: None | str | Unset = UNSET
    card_last4: None | str | Unset = UNSET
    role: UserCreateRole | Unset = UserCreateRole.CUSTOMER
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.address_model import AddressModel

        email = self.email

        password: None | str | Unset
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        first_name: None | str | Unset
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        address: dict[str, Any] | None | Unset
        if isinstance(self.address, Unset):
            address = UNSET
        elif isinstance(self.address, AddressModel):
            address = self.address.to_dict()
        else:
            address = self.address

        phone_number: None | str | Unset
        if isinstance(self.phone_number, Unset):
            phone_number = UNSET
        else:
            phone_number = self.phone_number

        card_last4: None | str | Unset
        if isinstance(self.card_last4, Unset):
            card_last4 = UNSET
        else:
            card_last4 = self.card_last4

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
            }
        )
        if password is not UNSET:
            field_dict["password"] = password
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if address is not UNSET:
            field_dict["address"] = address
        if phone_number is not UNSET:
            field_dict["phone_number"] = phone_number
        if card_last4 is not UNSET:
            field_dict["card_last4"] = card_last4
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.address_model import AddressModel

        d = dict(src_dict)
        email = d.pop("email")

        def _parse_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_first_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_address(data: object) -> AddressModel | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                address_type_0 = AddressModel.from_dict(data)

                return address_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AddressModel | None | Unset, data)

        address = _parse_address(d.pop("address", UNSET))

        def _parse_phone_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone_number = _parse_phone_number(d.pop("phone_number", UNSET))

        def _parse_card_last4(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        card_last4 = _parse_card_last4(d.pop("card_last4", UNSET))

        _role = d.pop("role", UNSET)
        role: UserCreateRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = UserCreateRole(_role)

        user_create = cls(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            address=address,
            phone_number=phone_number,
            card_last4=card_last4,
            role=role,
        )

        user_create.additional_properties = d
        return user_create

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

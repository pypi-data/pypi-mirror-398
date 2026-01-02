from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.backend_user_create_role_type_0 import BackendUserCreateRoleType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackendUserCreate")


@_attrs_define
class BackendUserCreate:
    """Model for creating a new backend user.

    Attributes:
        email (str):
        password (str): Password (8-72 characters)
        terms_accepted (bool): Must be True to accept terms and conditions
        privacy_accepted (bool): Must be True to accept privacy policy
        first_name (None | str | Unset):
        last_name (None | str | Unset):
        role (BackendUserCreateRoleType0 | None | Unset):
    """

    email: str
    password: str
    terms_accepted: bool
    privacy_accepted: bool
    first_name: None | str | Unset = UNSET
    last_name: None | str | Unset = UNSET
    role: BackendUserCreateRoleType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        password = self.password

        terms_accepted = self.terms_accepted

        privacy_accepted = self.privacy_accepted

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

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        elif isinstance(self.role, BackendUserCreateRoleType0):
            role = self.role.value
        else:
            role = self.role

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "password": password,
                "terms_accepted": terms_accepted,
                "privacy_accepted": privacy_accepted,
            }
        )
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        password = d.pop("password")

        terms_accepted = d.pop("terms_accepted")

        privacy_accepted = d.pop("privacy_accepted")

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

        def _parse_role(data: object) -> BackendUserCreateRoleType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                role_type_0 = BackendUserCreateRoleType0(data)

                return role_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BackendUserCreateRoleType0 | None | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        backend_user_create = cls(
            email=email,
            password=password,
            terms_accepted=terms_accepted,
            privacy_accepted=privacy_accepted,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )

        backend_user_create.additional_properties = d
        return backend_user_create

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

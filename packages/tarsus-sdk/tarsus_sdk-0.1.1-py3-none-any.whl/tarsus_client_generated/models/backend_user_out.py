from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.backend_user_out_role import BackendUserOutRole

T = TypeVar("T", bound="BackendUserOut")


@_attrs_define
class BackendUserOut:
    """Output model for backend user (simplified).

    Attributes:
        id (None | str):
        email (str):
        first_name (None | str):
        last_name (None | str):
        role (BackendUserOutRole):
        is_active (bool):
        created_at (datetime.datetime):
    """

    id: None | str
    email: str
    first_name: None | str
    last_name: None | str
    role: BackendUserOutRole
    is_active: bool
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        email = self.email

        first_name: None | str
        first_name = self.first_name

        last_name: None | str
        last_name = self.last_name

        role = self.role.value

        is_active = self.is_active

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": is_active,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        role = BackendUserOutRole(d.pop("role"))

        is_active = d.pop("is_active")

        created_at = isoparse(d.pop("created_at"))

        backend_user_out = cls(
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=is_active,
            created_at=created_at,
        )

        backend_user_out.additional_properties = d
        return backend_user_out

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

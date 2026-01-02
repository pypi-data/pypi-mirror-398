from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.api_key_type import APIKeyType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_create_response_endpoint_permissions import (
        APIKeyCreateResponseEndpointPermissions,
    )


T = TypeVar("T", bound="APIKeyCreateResponse")


@_attrs_define
class APIKeyCreateResponse:
    """Response when creating a new API key - includes the full key (shown only once).

    Attributes:
        id (str):
        key (str):
        key_prefix (str):
        name (str):
        description (None | str):
        key_type (APIKeyType): Type of API key - sandbox or production
        allowed_endpoints (list[str]):
        endpoint_permissions (APIKeyCreateResponseEndpointPermissions):
        is_active (bool):
        expires_at (datetime.datetime | None):
        created_at (datetime.datetime):
        warning (str | Unset):  Default: '⚠️ Save this key now! You will not be able to see it again.'.
    """

    id: str
    key: str
    key_prefix: str
    name: str
    description: None | str
    key_type: APIKeyType
    allowed_endpoints: list[str]
    endpoint_permissions: APIKeyCreateResponseEndpointPermissions
    is_active: bool
    expires_at: datetime.datetime | None
    created_at: datetime.datetime
    warning: str | Unset = "⚠️ Save this key now! You will not be able to see it again."
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        key = self.key

        key_prefix = self.key_prefix

        name = self.name

        description: None | str
        description = self.description

        key_type = self.key_type.value

        allowed_endpoints = self.allowed_endpoints

        endpoint_permissions = self.endpoint_permissions.to_dict()

        is_active = self.is_active

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        created_at = self.created_at.isoformat()

        warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "key": key,
                "key_prefix": key_prefix,
                "name": name,
                "description": description,
                "key_type": key_type,
                "allowed_endpoints": allowed_endpoints,
                "endpoint_permissions": endpoint_permissions,
                "is_active": is_active,
                "expires_at": expires_at,
                "created_at": created_at,
            }
        )
        if warning is not UNSET:
            field_dict["warning"] = warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_create_response_endpoint_permissions import (
            APIKeyCreateResponseEndpointPermissions,
        )

        d = dict(src_dict)
        id = d.pop("id")

        key = d.pop("key")

        key_prefix = d.pop("key_prefix")

        name = d.pop("name")

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        key_type = APIKeyType(d.pop("key_type"))

        allowed_endpoints = cast(list[str], d.pop("allowed_endpoints"))

        endpoint_permissions = APIKeyCreateResponseEndpointPermissions.from_dict(d.pop("endpoint_permissions"))

        is_active = d.pop("is_active")

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        created_at = isoparse(d.pop("created_at"))

        warning = d.pop("warning", UNSET)

        api_key_create_response = cls(
            id=id,
            key=key,
            key_prefix=key_prefix,
            name=name,
            description=description,
            key_type=key_type,
            allowed_endpoints=allowed_endpoints,
            endpoint_permissions=endpoint_permissions,
            is_active=is_active,
            expires_at=expires_at,
            created_at=created_at,
            warning=warning,
        )

        api_key_create_response.additional_properties = d
        return api_key_create_response

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

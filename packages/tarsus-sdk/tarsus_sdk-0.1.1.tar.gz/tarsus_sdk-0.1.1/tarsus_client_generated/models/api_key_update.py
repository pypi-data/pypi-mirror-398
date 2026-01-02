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
    from ..models.api_key_update_endpoint_permissions_type_0 import (
        APIKeyUpdateEndpointPermissionsType0,
    )


T = TypeVar("T", bound="APIKeyUpdate")


@_attrs_define
class APIKeyUpdate:
    """Model for updating an API key.

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        key_type (APIKeyType | None | Unset):
        allowed_endpoints (list[str] | None | Unset): List of allowed endpoint paths. Empty list means all endpoints
            (master key). DEPRECATED: Use endpoint_permissions instead.
        endpoint_permissions (APIKeyUpdateEndpointPermissionsType0 | None | Unset): Dictionary mapping endpoint paths to
            permission types. Format: {'/api/v1/products/*': ['read', 'write']}. Empty dict means all endpoints with all
            permissions (master key).
        is_active (bool | None | Unset):
        expires_at (datetime.datetime | None | Unset):
        rate_limit_per_minute (int | None | Unset): Maximum requests per minute. None uses subscription tier default.
        rate_limit_per_hour (int | None | Unset): Maximum requests per hour. None uses subscription tier default.
        rate_limit_per_day (int | None | Unset): Maximum requests per day. None uses subscription tier default.
        scopes (list[str] | None | Unset): Legacy field - maps to allowed_endpoints
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    key_type: APIKeyType | None | Unset = UNSET
    allowed_endpoints: list[str] | None | Unset = UNSET
    endpoint_permissions: APIKeyUpdateEndpointPermissionsType0 | None | Unset = UNSET
    is_active: bool | None | Unset = UNSET
    expires_at: datetime.datetime | None | Unset = UNSET
    rate_limit_per_minute: int | None | Unset = UNSET
    rate_limit_per_hour: int | None | Unset = UNSET
    rate_limit_per_day: int | None | Unset = UNSET
    scopes: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.api_key_update_endpoint_permissions_type_0 import (
            APIKeyUpdateEndpointPermissionsType0,
        )

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        key_type: None | str | Unset
        if isinstance(self.key_type, Unset):
            key_type = UNSET
        elif isinstance(self.key_type, APIKeyType):
            key_type = self.key_type.value
        else:
            key_type = self.key_type

        allowed_endpoints: list[str] | None | Unset
        if isinstance(self.allowed_endpoints, Unset):
            allowed_endpoints = UNSET
        elif isinstance(self.allowed_endpoints, list):
            allowed_endpoints = self.allowed_endpoints

        else:
            allowed_endpoints = self.allowed_endpoints

        endpoint_permissions: dict[str, Any] | None | Unset
        if isinstance(self.endpoint_permissions, Unset):
            endpoint_permissions = UNSET
        elif isinstance(self.endpoint_permissions, APIKeyUpdateEndpointPermissionsType0):
            endpoint_permissions = self.endpoint_permissions.to_dict()
        else:
            endpoint_permissions = self.endpoint_permissions

        is_active: bool | None | Unset
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        elif isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        rate_limit_per_minute: int | None | Unset
        if isinstance(self.rate_limit_per_minute, Unset):
            rate_limit_per_minute = UNSET
        else:
            rate_limit_per_minute = self.rate_limit_per_minute

        rate_limit_per_hour: int | None | Unset
        if isinstance(self.rate_limit_per_hour, Unset):
            rate_limit_per_hour = UNSET
        else:
            rate_limit_per_hour = self.rate_limit_per_hour

        rate_limit_per_day: int | None | Unset
        if isinstance(self.rate_limit_per_day, Unset):
            rate_limit_per_day = UNSET
        else:
            rate_limit_per_day = self.rate_limit_per_day

        scopes: list[str] | None | Unset
        if isinstance(self.scopes, Unset):
            scopes = UNSET
        elif isinstance(self.scopes, list):
            scopes = self.scopes

        else:
            scopes = self.scopes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if key_type is not UNSET:
            field_dict["key_type"] = key_type
        if allowed_endpoints is not UNSET:
            field_dict["allowed_endpoints"] = allowed_endpoints
        if endpoint_permissions is not UNSET:
            field_dict["endpoint_permissions"] = endpoint_permissions
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if rate_limit_per_minute is not UNSET:
            field_dict["rate_limit_per_minute"] = rate_limit_per_minute
        if rate_limit_per_hour is not UNSET:
            field_dict["rate_limit_per_hour"] = rate_limit_per_hour
        if rate_limit_per_day is not UNSET:
            field_dict["rate_limit_per_day"] = rate_limit_per_day
        if scopes is not UNSET:
            field_dict["scopes"] = scopes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_update_endpoint_permissions_type_0 import (
            APIKeyUpdateEndpointPermissionsType0,
        )

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_key_type(data: object) -> APIKeyType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                key_type_type_0 = APIKeyType(data)

                return key_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(APIKeyType | None | Unset, data)

        key_type = _parse_key_type(d.pop("key_type", UNSET))

        def _parse_allowed_endpoints(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                allowed_endpoints_type_0 = cast(list[str], data)

                return allowed_endpoints_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        allowed_endpoints = _parse_allowed_endpoints(d.pop("allowed_endpoints", UNSET))

        def _parse_endpoint_permissions(
            data: object,
        ) -> APIKeyUpdateEndpointPermissionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                endpoint_permissions_type_0 = APIKeyUpdateEndpointPermissionsType0.from_dict(data)

                return endpoint_permissions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(APIKeyUpdateEndpointPermissionsType0 | None | Unset, data)

        endpoint_permissions = _parse_endpoint_permissions(d.pop("endpoint_permissions", UNSET))

        def _parse_is_active(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        def _parse_expires_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        def _parse_rate_limit_per_minute(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rate_limit_per_minute = _parse_rate_limit_per_minute(d.pop("rate_limit_per_minute", UNSET))

        def _parse_rate_limit_per_hour(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rate_limit_per_hour = _parse_rate_limit_per_hour(d.pop("rate_limit_per_hour", UNSET))

        def _parse_rate_limit_per_day(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rate_limit_per_day = _parse_rate_limit_per_day(d.pop("rate_limit_per_day", UNSET))

        def _parse_scopes(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                scopes_type_0 = cast(list[str], data)

                return scopes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        scopes = _parse_scopes(d.pop("scopes", UNSET))

        api_key_update = cls(
            name=name,
            description=description,
            key_type=key_type,
            allowed_endpoints=allowed_endpoints,
            endpoint_permissions=endpoint_permissions,
            is_active=is_active,
            expires_at=expires_at,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            scopes=scopes,
        )

        api_key_update.additional_properties = d
        return api_key_update

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

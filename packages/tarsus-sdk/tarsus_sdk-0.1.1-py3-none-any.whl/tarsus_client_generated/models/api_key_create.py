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
    from ..models.api_key_create_endpoint_permissions_type_0 import (
        APIKeyCreateEndpointPermissionsType0,
    )


T = TypeVar("T", bound="APIKeyCreate")


@_attrs_define
class APIKeyCreate:
    """Model for creating a new API key.

    Attributes:
        name (str):
        description (None | str | Unset):
        key_type (APIKeyType | Unset): Type of API key - sandbox or production
        allowed_endpoints (list[str] | None | Unset): List of allowed endpoint paths. Empty list or None means all
            endpoints (master key). DEPRECATED: Use endpoint_permissions instead.
        endpoint_permissions (APIKeyCreateEndpointPermissionsType0 | None | Unset): Dictionary mapping endpoint paths to
            permission types. Format: {'/api/v1/products/*': ['read', 'write']}. Empty dict or None means all endpoints with
            all permissions (master key).
        expires_at (datetime.datetime | None | Unset):
        project_id (None | str | Unset): ID of the project this key is associated with (optional)
        rate_limit_per_minute (int | None | Unset): Maximum requests per minute. None uses subscription tier default.
        rate_limit_per_hour (int | None | Unset): Maximum requests per hour. None uses subscription tier default.
        rate_limit_per_day (int | None | Unset): Maximum requests per day. None uses subscription tier default.
        scopes (list[str] | None | Unset): Legacy field - maps to allowed_endpoints
    """

    name: str
    description: None | str | Unset = UNSET
    key_type: APIKeyType | Unset = UNSET
    allowed_endpoints: list[str] | None | Unset = UNSET
    endpoint_permissions: APIKeyCreateEndpointPermissionsType0 | None | Unset = UNSET
    expires_at: datetime.datetime | None | Unset = UNSET
    project_id: None | str | Unset = UNSET
    rate_limit_per_minute: int | None | Unset = UNSET
    rate_limit_per_hour: int | None | Unset = UNSET
    rate_limit_per_day: int | None | Unset = UNSET
    scopes: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.api_key_create_endpoint_permissions_type_0 import (
            APIKeyCreateEndpointPermissionsType0,
        )

        name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        key_type: str | Unset = UNSET
        if not isinstance(self.key_type, Unset):
            key_type = self.key_type.value

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
        elif isinstance(self.endpoint_permissions, APIKeyCreateEndpointPermissionsType0):
            endpoint_permissions = self.endpoint_permissions.to_dict()
        else:
            endpoint_permissions = self.endpoint_permissions

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        elif isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

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
        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if key_type is not UNSET:
            field_dict["key_type"] = key_type
        if allowed_endpoints is not UNSET:
            field_dict["allowed_endpoints"] = allowed_endpoints
        if endpoint_permissions is not UNSET:
            field_dict["endpoint_permissions"] = endpoint_permissions
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
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
        from ..models.api_key_create_endpoint_permissions_type_0 import (
            APIKeyCreateEndpointPermissionsType0,
        )

        d = dict(src_dict)
        name = d.pop("name")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _key_type = d.pop("key_type", UNSET)
        key_type: APIKeyType | Unset
        if isinstance(_key_type, Unset):
            key_type = UNSET
        else:
            key_type = APIKeyType(_key_type)

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
        ) -> APIKeyCreateEndpointPermissionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                endpoint_permissions_type_0 = APIKeyCreateEndpointPermissionsType0.from_dict(data)

                return endpoint_permissions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(APIKeyCreateEndpointPermissionsType0 | None | Unset, data)

        endpoint_permissions = _parse_endpoint_permissions(d.pop("endpoint_permissions", UNSET))

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

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

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

        api_key_create = cls(
            name=name,
            description=description,
            key_type=key_type,
            allowed_endpoints=allowed_endpoints,
            endpoint_permissions=endpoint_permissions,
            expires_at=expires_at,
            project_id=project_id,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            scopes=scopes,
        )

        api_key_create.additional_properties = d
        return api_key_create

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

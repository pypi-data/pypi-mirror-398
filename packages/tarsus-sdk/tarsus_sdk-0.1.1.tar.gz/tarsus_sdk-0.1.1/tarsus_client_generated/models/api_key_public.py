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
    from ..models.api_key_public_endpoint_permissions import (
        APIKeyPublicEndpointPermissions,
    )


T = TypeVar("T", bound="APIKeyPublic")


@_attrs_define
class APIKeyPublic:
    """Public representation of an API key (without sensitive data).

    Attributes:
        id (None | str):
        key_prefix (str):
        backend_user_id (str):
        name (str):
        description (None | str):
        key_type (APIKeyType): Type of API key - sandbox or production
        allowed_endpoints (list[str]):
        endpoint_permissions (APIKeyPublicEndpointPermissions):
        is_active (bool):
        last_used_at (datetime.datetime | None):
        expires_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime | None):
        project_id (None | str | Unset):
        rate_limit_per_minute (int | None | Unset):
        rate_limit_per_hour (int | None | Unset):
        rate_limit_per_day (int | None | Unset):
    """

    id: None | str
    key_prefix: str
    backend_user_id: str
    name: str
    description: None | str
    key_type: APIKeyType
    allowed_endpoints: list[str]
    endpoint_permissions: APIKeyPublicEndpointPermissions
    is_active: bool
    last_used_at: datetime.datetime | None
    expires_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    project_id: None | str | Unset = UNSET
    rate_limit_per_minute: int | None | Unset = UNSET
    rate_limit_per_hour: int | None | Unset = UNSET
    rate_limit_per_day: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        key_prefix = self.key_prefix

        backend_user_id = self.backend_user_id

        name = self.name

        description: None | str
        description = self.description

        key_type = self.key_type.value

        allowed_endpoints = self.allowed_endpoints

        endpoint_permissions = self.endpoint_permissions.to_dict()

        is_active = self.is_active

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        created_at = self.created_at.isoformat()

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "key_prefix": key_prefix,
                "backend_user_id": backend_user_id,
                "name": name,
                "description": description,
                "key_type": key_type,
                "allowed_endpoints": allowed_endpoints,
                "endpoint_permissions": endpoint_permissions,
                "is_active": is_active,
                "last_used_at": last_used_at,
                "expires_at": expires_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if rate_limit_per_minute is not UNSET:
            field_dict["rate_limit_per_minute"] = rate_limit_per_minute
        if rate_limit_per_hour is not UNSET:
            field_dict["rate_limit_per_hour"] = rate_limit_per_hour
        if rate_limit_per_day is not UNSET:
            field_dict["rate_limit_per_day"] = rate_limit_per_day

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_public_endpoint_permissions import (
            APIKeyPublicEndpointPermissions,
        )

        d = dict(src_dict)

        def _parse_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        id = _parse_id(d.pop("id"))

        key_prefix = d.pop("key_prefix")

        backend_user_id = d.pop("backend_user_id")

        name = d.pop("name")

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        key_type = APIKeyType(d.pop("key_type"))

        allowed_endpoints = cast(list[str], d.pop("allowed_endpoints"))

        endpoint_permissions = APIKeyPublicEndpointPermissions.from_dict(d.pop("endpoint_permissions"))

        is_active = d.pop("is_active")

        def _parse_last_used_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = isoparse(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

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

        def _parse_updated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at"))

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

        api_key_public = cls(
            id=id,
            key_prefix=key_prefix,
            backend_user_id=backend_user_id,
            name=name,
            description=description,
            key_type=key_type,
            allowed_endpoints=allowed_endpoints,
            endpoint_permissions=endpoint_permissions,
            is_active=is_active,
            last_used_at=last_used_at,
            expires_at=expires_at,
            created_at=created_at,
            updated_at=updated_at,
            project_id=project_id,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
        )

        api_key_public.additional_properties = d
        return api_key_public

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

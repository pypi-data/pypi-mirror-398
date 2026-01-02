from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.platform_key_status import PlatformKeyStatus
from ..models.platform_key_type import PlatformKeyType

T = TypeVar("T", bound="PlatformKeyPublic")


@_attrs_define
class PlatformKeyPublic:
    """Public representation of platform key (without sensitive credentials)

    Attributes:
        id (None | str):
        key_type (PlatformKeyType): Type of platform key
        status (PlatformKeyStatus): Status of platform key
        usage_limit (int | None):
        usage_count (int):
        usage_reset_at (datetime.datetime | None):
        description (None | str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime | None):
    """

    id: None | str
    key_type: PlatformKeyType
    status: PlatformKeyStatus
    usage_limit: int | None
    usage_count: int
    usage_reset_at: datetime.datetime | None
    description: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        key_type = self.key_type.value

        status = self.status.value

        usage_limit: int | None
        usage_limit = self.usage_limit

        usage_count = self.usage_count

        usage_reset_at: None | str
        if isinstance(self.usage_reset_at, datetime.datetime):
            usage_reset_at = self.usage_reset_at.isoformat()
        else:
            usage_reset_at = self.usage_reset_at

        description: None | str
        description = self.description

        created_at = self.created_at.isoformat()

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "key_type": key_type,
                "status": status,
                "usage_limit": usage_limit,
                "usage_count": usage_count,
                "usage_reset_at": usage_reset_at,
                "description": description,
                "created_at": created_at,
                "updated_at": updated_at,
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

        key_type = PlatformKeyType(d.pop("key_type"))

        status = PlatformKeyStatus(d.pop("status"))

        def _parse_usage_limit(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        usage_limit = _parse_usage_limit(d.pop("usage_limit"))

        usage_count = d.pop("usage_count")

        def _parse_usage_reset_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                usage_reset_at_type_0 = isoparse(data)

                return usage_reset_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        usage_reset_at = _parse_usage_reset_at(d.pop("usage_reset_at"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

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

        platform_key_public = cls(
            id=id,
            key_type=key_type,
            status=status,
            usage_limit=usage_limit,
            usage_count=usage_count,
            usage_reset_at=usage_reset_at,
            description=description,
            created_at=created_at,
            updated_at=updated_at,
        )

        platform_key_public.additional_properties = d
        return platform_key_public

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

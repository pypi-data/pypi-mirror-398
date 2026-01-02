from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.origin_environment import OriginEnvironment
from ..types import UNSET, Unset

T = TypeVar("T", bound="AllowedOrigin")


@_attrs_define
class AllowedOrigin:
    """Model for a single allowed origin with environment tag.

    Attributes:
        origin (str): The origin URL (e.g., https://example.com)
        environment (OriginEnvironment | Unset): Environment tag for allowed origins
        created_at (datetime.datetime | Unset):
    """

    origin: str
    environment: OriginEnvironment | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        origin = self.origin

        environment: str | Unset = UNSET
        if not isinstance(self.environment, Unset):
            environment = self.environment.value

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "origin": origin,
            }
        )
        if environment is not UNSET:
            field_dict["environment"] = environment
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        origin = d.pop("origin")

        _environment = d.pop("environment", UNSET)
        environment: OriginEnvironment | Unset
        if isinstance(_environment, Unset):
            environment = UNSET
        else:
            environment = OriginEnvironment(_environment)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        allowed_origin = cls(
            origin=origin,
            environment=environment,
            created_at=created_at,
        )

        allowed_origin.additional_properties = d
        return allowed_origin

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

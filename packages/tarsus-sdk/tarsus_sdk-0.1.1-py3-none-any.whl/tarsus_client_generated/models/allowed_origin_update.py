from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.origin_environment import OriginEnvironment
from ..types import UNSET, Unset

T = TypeVar("T", bound="AllowedOriginUpdate")


@_attrs_define
class AllowedOriginUpdate:
    """Model for updating allowed origins.

    Attributes:
        origin (str): The origin URL (e.g., https://example.com)
        environment (OriginEnvironment | Unset): Environment tag for allowed origins
    """

    origin: str
    environment: OriginEnvironment | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        origin = self.origin

        environment: str | Unset = UNSET
        if not isinstance(self.environment, Unset):
            environment = self.environment.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "origin": origin,
            }
        )
        if environment is not UNSET:
            field_dict["environment"] = environment

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

        allowed_origin_update = cls(
            origin=origin,
            environment=environment,
        )

        allowed_origin_update.additional_properties = d
        return allowed_origin_update

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

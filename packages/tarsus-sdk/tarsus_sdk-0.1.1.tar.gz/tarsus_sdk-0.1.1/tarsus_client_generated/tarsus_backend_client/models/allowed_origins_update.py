from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.allowed_origin_update import AllowedOriginUpdate


T = TypeVar("T", bound="AllowedOriginsUpdate")


@_attrs_define
class AllowedOriginsUpdate:
    """Model for updating project allowed origins.

    Attributes:
        origins (list[AllowedOriginUpdate]): List of allowed origins
    """

    origins: list[AllowedOriginUpdate]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        origins = []
        for origins_item_data in self.origins:
            origins_item = origins_item_data.to_dict()
            origins.append(origins_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "origins": origins,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.allowed_origin_update import AllowedOriginUpdate

        d = dict(src_dict)
        origins = []
        _origins = d.pop("origins")
        for origins_item_data in _origins:
            origins_item = AllowedOriginUpdate.from_dict(origins_item_data)

            origins.append(origins_item)

        allowed_origins_update = cls(
            origins=origins,
        )

        allowed_origins_update.additional_properties = d
        return allowed_origins_update

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

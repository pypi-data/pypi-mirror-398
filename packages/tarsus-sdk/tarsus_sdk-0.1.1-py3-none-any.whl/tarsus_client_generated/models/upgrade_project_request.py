from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpgradeProjectRequest")


@_attrs_define
class UpgradeProjectRequest:
    """Request model for upgrading a project to live.

    Attributes:
        billing_interval (str | Unset):  Default: 'month'.
    """

    billing_interval: str | Unset = "month"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        billing_interval = self.billing_interval

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if billing_interval is not UNSET:
            field_dict["billing_interval"] = billing_interval

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        billing_interval = d.pop("billing_interval", UNSET)

        upgrade_project_request = cls(
            billing_interval=billing_interval,
        )

        upgrade_project_request.additional_properties = d
        return upgrade_project_request

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

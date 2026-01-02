from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseActivationModel")


@_attrs_define
class LicenseActivationModel:
    """Individual device activation (stored in subcollection)

    Attributes:
        device_id (str):
        device_name (None | str | Unset):
        activated_at (datetime.datetime | Unset):
        last_seen (datetime.datetime | Unset):
    """

    device_id: str
    device_name: None | str | Unset = UNSET
    activated_at: datetime.datetime | Unset = UNSET
    last_seen: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        device_id = self.device_id

        device_name: None | str | Unset
        if isinstance(self.device_name, Unset):
            device_name = UNSET
        else:
            device_name = self.device_name

        activated_at: str | Unset = UNSET
        if not isinstance(self.activated_at, Unset):
            activated_at = self.activated_at.isoformat()

        last_seen: str | Unset = UNSET
        if not isinstance(self.last_seen, Unset):
            last_seen = self.last_seen.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "device_id": device_id,
            }
        )
        if device_name is not UNSET:
            field_dict["device_name"] = device_name
        if activated_at is not UNSET:
            field_dict["activated_at"] = activated_at
        if last_seen is not UNSET:
            field_dict["last_seen"] = last_seen

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device_id = d.pop("device_id")

        def _parse_device_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        device_name = _parse_device_name(d.pop("device_name", UNSET))

        _activated_at = d.pop("activated_at", UNSET)
        activated_at: datetime.datetime | Unset
        if isinstance(_activated_at, Unset):
            activated_at = UNSET
        else:
            activated_at = isoparse(_activated_at)

        _last_seen = d.pop("last_seen", UNSET)
        last_seen: datetime.datetime | Unset
        if isinstance(_last_seen, Unset):
            last_seen = UNSET
        else:
            last_seen = isoparse(_last_seen)

        license_activation_model = cls(
            device_id=device_id,
            device_name=device_name,
            activated_at=activated_at,
            last_seen=last_seen,
        )

        license_activation_model.additional_properties = d
        return license_activation_model

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

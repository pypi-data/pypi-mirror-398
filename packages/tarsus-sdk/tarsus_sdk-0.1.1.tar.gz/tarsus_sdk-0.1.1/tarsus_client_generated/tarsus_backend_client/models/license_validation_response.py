from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.license_status import LicenseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseValidationResponse")


@_attrs_define
class LicenseValidationResponse:
    """Response model for license validation

    Attributes:
        is_valid (bool):
        message (str):
        license_key (None | str | Unset):
        status (LicenseStatus | None | Unset):
        activation_count (int | Unset):  Default: 0.
        max_activations (int | Unset):  Default: 5.
    """

    is_valid: bool
    message: str
    license_key: None | str | Unset = UNSET
    status: LicenseStatus | None | Unset = UNSET
    activation_count: int | Unset = 0
    max_activations: int | Unset = 5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_valid = self.is_valid

        message = self.message

        license_key: None | str | Unset
        if isinstance(self.license_key, Unset):
            license_key = UNSET
        else:
            license_key = self.license_key

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, LicenseStatus):
            status = self.status.value
        else:
            status = self.status

        activation_count = self.activation_count

        max_activations = self.max_activations

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "is_valid": is_valid,
                "message": message,
            }
        )
        if license_key is not UNSET:
            field_dict["license_key"] = license_key
        if status is not UNSET:
            field_dict["status"] = status
        if activation_count is not UNSET:
            field_dict["activation_count"] = activation_count
        if max_activations is not UNSET:
            field_dict["max_activations"] = max_activations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_valid = d.pop("is_valid")

        message = d.pop("message")

        def _parse_license_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        license_key = _parse_license_key(d.pop("license_key", UNSET))

        def _parse_status(data: object) -> LicenseStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = LicenseStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(LicenseStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        activation_count = d.pop("activation_count", UNSET)

        max_activations = d.pop("max_activations", UNSET)

        license_validation_response = cls(
            is_valid=is_valid,
            message=message,
            license_key=license_key,
            status=status,
            activation_count=activation_count,
            max_activations=max_activations,
        )

        license_validation_response.additional_properties = d
        return license_validation_response

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

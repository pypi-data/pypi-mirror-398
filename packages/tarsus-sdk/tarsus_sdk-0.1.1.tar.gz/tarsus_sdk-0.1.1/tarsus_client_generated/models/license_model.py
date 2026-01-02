from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.license_status import LicenseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="LicenseModel")


@_attrs_define
class LicenseModel:
    """License key document (document ID is the license key)

    Attributes:
        user_id (str):
        order_id (str):
        product_id (str):
        variant_id (None | str | Unset):
        status (LicenseStatus | Unset):
        valid_until (datetime.datetime | None | Unset):
        max_activations (int | Unset):  Default: 5.
        activation_count (int | Unset):  Default: 0.
        created_at (datetime.datetime | Unset):
    """

    user_id: str
    order_id: str
    product_id: str
    variant_id: None | str | Unset = UNSET
    status: LicenseStatus | Unset = UNSET
    valid_until: datetime.datetime | None | Unset = UNSET
    max_activations: int | Unset = 5
    activation_count: int | Unset = 0
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        order_id = self.order_id

        product_id = self.product_id

        variant_id: None | str | Unset
        if isinstance(self.variant_id, Unset):
            variant_id = UNSET
        else:
            variant_id = self.variant_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        valid_until: None | str | Unset
        if isinstance(self.valid_until, Unset):
            valid_until = UNSET
        elif isinstance(self.valid_until, datetime.datetime):
            valid_until = self.valid_until.isoformat()
        else:
            valid_until = self.valid_until

        max_activations = self.max_activations

        activation_count = self.activation_count

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "order_id": order_id,
                "product_id": product_id,
            }
        )
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if status is not UNSET:
            field_dict["status"] = status
        if valid_until is not UNSET:
            field_dict["valid_until"] = valid_until
        if max_activations is not UNSET:
            field_dict["max_activations"] = max_activations
        if activation_count is not UNSET:
            field_dict["activation_count"] = activation_count
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        order_id = d.pop("order_id")

        product_id = d.pop("product_id")

        def _parse_variant_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        variant_id = _parse_variant_id(d.pop("variant_id", UNSET))

        _status = d.pop("status", UNSET)
        status: LicenseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = LicenseStatus(_status)

        def _parse_valid_until(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                valid_until_type_0 = isoparse(data)

                return valid_until_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        valid_until = _parse_valid_until(d.pop("valid_until", UNSET))

        max_activations = d.pop("max_activations", UNSET)

        activation_count = d.pop("activation_count", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        license_model = cls(
            user_id=user_id,
            order_id=order_id,
            product_id=product_id,
            variant_id=variant_id,
            status=status,
            valid_until=valid_until,
            max_activations=max_activations,
            activation_count=activation_count,
            created_at=created_at,
        )

        license_model.additional_properties = d
        return license_model

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

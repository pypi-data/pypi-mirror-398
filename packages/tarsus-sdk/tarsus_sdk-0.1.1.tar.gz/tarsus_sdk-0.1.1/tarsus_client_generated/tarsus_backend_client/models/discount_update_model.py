from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.discount_status import DiscountStatus
from ..models.discount_type import DiscountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.discount_update_model_applies_to_type_0 import DiscountUpdateModelAppliesToType0


T = TypeVar("T", bound="DiscountUpdateModel")


@_attrs_define
class DiscountUpdateModel:
    """Model for updating discounts

    Attributes:
        code (None | str | Unset):
        type_ (DiscountType | None | Unset):
        value (float | None | Unset):
        status (DiscountStatus | None | Unset):
        valid_from (datetime.datetime | None | Unset):
        valid_until (datetime.datetime | None | Unset):
        usage_limit (int | None | Unset):
        min_cart_value (float | None | Unset):
        applies_to (DiscountUpdateModelAppliesToType0 | None | Unset):
        applies_to_flat (list[str] | None | Unset):
        updated_at (datetime.datetime | Unset):
    """

    code: None | str | Unset = UNSET
    type_: DiscountType | None | Unset = UNSET
    value: float | None | Unset = UNSET
    status: DiscountStatus | None | Unset = UNSET
    valid_from: datetime.datetime | None | Unset = UNSET
    valid_until: datetime.datetime | None | Unset = UNSET
    usage_limit: int | None | Unset = UNSET
    min_cart_value: float | None | Unset = UNSET
    applies_to: DiscountUpdateModelAppliesToType0 | None | Unset = UNSET
    applies_to_flat: list[str] | None | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.discount_update_model_applies_to_type_0 import DiscountUpdateModelAppliesToType0

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, DiscountType):
            type_ = self.type_.value
        else:
            type_ = self.type_

        value: float | None | Unset
        if isinstance(self.value, Unset):
            value = UNSET
        else:
            value = self.value

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, DiscountStatus):
            status = self.status.value
        else:
            status = self.status

        valid_from: None | str | Unset
        if isinstance(self.valid_from, Unset):
            valid_from = UNSET
        elif isinstance(self.valid_from, datetime.datetime):
            valid_from = self.valid_from.isoformat()
        else:
            valid_from = self.valid_from

        valid_until: None | str | Unset
        if isinstance(self.valid_until, Unset):
            valid_until = UNSET
        elif isinstance(self.valid_until, datetime.datetime):
            valid_until = self.valid_until.isoformat()
        else:
            valid_until = self.valid_until

        usage_limit: int | None | Unset
        if isinstance(self.usage_limit, Unset):
            usage_limit = UNSET
        else:
            usage_limit = self.usage_limit

        min_cart_value: float | None | Unset
        if isinstance(self.min_cart_value, Unset):
            min_cart_value = UNSET
        else:
            min_cart_value = self.min_cart_value

        applies_to: dict[str, Any] | None | Unset
        if isinstance(self.applies_to, Unset):
            applies_to = UNSET
        elif isinstance(self.applies_to, DiscountUpdateModelAppliesToType0):
            applies_to = self.applies_to.to_dict()
        else:
            applies_to = self.applies_to

        applies_to_flat: list[str] | None | Unset
        if isinstance(self.applies_to_flat, Unset):
            applies_to_flat = UNSET
        elif isinstance(self.applies_to_flat, list):
            applies_to_flat = self.applies_to_flat

        else:
            applies_to_flat = self.applies_to_flat

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if code is not UNSET:
            field_dict["code"] = code
        if type_ is not UNSET:
            field_dict["type"] = type_
        if value is not UNSET:
            field_dict["value"] = value
        if status is not UNSET:
            field_dict["status"] = status
        if valid_from is not UNSET:
            field_dict["valid_from"] = valid_from
        if valid_until is not UNSET:
            field_dict["valid_until"] = valid_until
        if usage_limit is not UNSET:
            field_dict["usage_limit"] = usage_limit
        if min_cart_value is not UNSET:
            field_dict["min_cart_value"] = min_cart_value
        if applies_to is not UNSET:
            field_dict["applies_to"] = applies_to
        if applies_to_flat is not UNSET:
            field_dict["applies_to_flat"] = applies_to_flat
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.discount_update_model_applies_to_type_0 import DiscountUpdateModelAppliesToType0

        d = dict(src_dict)

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        def _parse_type_(data: object) -> DiscountType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = DiscountType(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DiscountType | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        value = _parse_value(d.pop("value", UNSET))

        def _parse_status(data: object) -> DiscountStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = DiscountStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DiscountStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_valid_from(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                valid_from_type_0 = isoparse(data)

                return valid_from_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        valid_from = _parse_valid_from(d.pop("valid_from", UNSET))

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

        def _parse_usage_limit(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        usage_limit = _parse_usage_limit(d.pop("usage_limit", UNSET))

        def _parse_min_cart_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        min_cart_value = _parse_min_cart_value(d.pop("min_cart_value", UNSET))

        def _parse_applies_to(data: object) -> DiscountUpdateModelAppliesToType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                applies_to_type_0 = DiscountUpdateModelAppliesToType0.from_dict(data)

                return applies_to_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DiscountUpdateModelAppliesToType0 | None | Unset, data)

        applies_to = _parse_applies_to(d.pop("applies_to", UNSET))

        def _parse_applies_to_flat(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                applies_to_flat_type_0 = cast(list[str], data)

                return applies_to_flat_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        applies_to_flat = _parse_applies_to_flat(d.pop("applies_to_flat", UNSET))

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        discount_update_model = cls(
            code=code,
            type_=type_,
            value=value,
            status=status,
            valid_from=valid_from,
            valid_until=valid_until,
            usage_limit=usage_limit,
            min_cart_value=min_cart_value,
            applies_to=applies_to,
            applies_to_flat=applies_to_flat,
            updated_at=updated_at,
        )

        discount_update_model.additional_properties = d
        return discount_update_model

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

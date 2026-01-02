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
    from ..models.discount_model_applies_to import DiscountModelAppliesTo


T = TypeVar("T", bound="DiscountModel")


@_attrs_define
class DiscountModel:
    """Discount/coupon definition

    Attributes:
        tenant_id (str):
        type_ (DiscountType):
        value (float):
        valid_from (datetime.datetime):
        valid_until (datetime.datetime):
        id (None | str | Unset):
        code (None | str | Unset):
        status (DiscountStatus | Unset):
        usage_limit (int | None | Unset):
        usage_count (int | Unset):  Default: 0.
        min_cart_value (float | None | Unset):
        applies_to (DiscountModelAppliesTo | Unset):
        applies_to_flat (list[str] | None | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
    """

    tenant_id: str
    type_: DiscountType
    value: float
    valid_from: datetime.datetime
    valid_until: datetime.datetime
    id: None | str | Unset = UNSET
    code: None | str | Unset = UNSET
    status: DiscountStatus | Unset = UNSET
    usage_limit: int | None | Unset = UNSET
    usage_count: int | Unset = 0
    min_cart_value: float | None | Unset = UNSET
    applies_to: DiscountModelAppliesTo | Unset = UNSET
    applies_to_flat: list[str] | None | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        type_ = self.type_.value

        value = self.value

        valid_from = self.valid_from.isoformat()

        valid_until = self.valid_until.isoformat()

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        code: None | str | Unset
        if isinstance(self.code, Unset):
            code = UNSET
        else:
            code = self.code

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        usage_limit: int | None | Unset
        if isinstance(self.usage_limit, Unset):
            usage_limit = UNSET
        else:
            usage_limit = self.usage_limit

        usage_count = self.usage_count

        min_cart_value: float | None | Unset
        if isinstance(self.min_cart_value, Unset):
            min_cart_value = UNSET
        else:
            min_cart_value = self.min_cart_value

        applies_to: dict[str, Any] | Unset = UNSET
        if not isinstance(self.applies_to, Unset):
            applies_to = self.applies_to.to_dict()

        applies_to_flat: list[str] | None | Unset
        if isinstance(self.applies_to_flat, Unset):
            applies_to_flat = UNSET
        elif isinstance(self.applies_to_flat, list):
            applies_to_flat = self.applies_to_flat

        else:
            applies_to_flat = self.applies_to_flat

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenant_id": tenant_id,
                "type": type_,
                "value": value,
                "valid_from": valid_from,
                "valid_until": valid_until,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if code is not UNSET:
            field_dict["code"] = code
        if status is not UNSET:
            field_dict["status"] = status
        if usage_limit is not UNSET:
            field_dict["usage_limit"] = usage_limit
        if usage_count is not UNSET:
            field_dict["usage_count"] = usage_count
        if min_cart_value is not UNSET:
            field_dict["min_cart_value"] = min_cart_value
        if applies_to is not UNSET:
            field_dict["applies_to"] = applies_to
        if applies_to_flat is not UNSET:
            field_dict["applies_to_flat"] = applies_to_flat
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.discount_model_applies_to import DiscountModelAppliesTo

        d = dict(src_dict)
        tenant_id = d.pop("tenant_id")

        type_ = DiscountType(d.pop("type"))

        value = d.pop("value")

        valid_from = isoparse(d.pop("valid_from"))

        valid_until = isoparse(d.pop("valid_until"))

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        code = _parse_code(d.pop("code", UNSET))

        _status = d.pop("status", UNSET)
        status: DiscountStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DiscountStatus(_status)

        def _parse_usage_limit(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        usage_limit = _parse_usage_limit(d.pop("usage_limit", UNSET))

        usage_count = d.pop("usage_count", UNSET)

        def _parse_min_cart_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        min_cart_value = _parse_min_cart_value(d.pop("min_cart_value", UNSET))

        _applies_to = d.pop("applies_to", UNSET)
        applies_to: DiscountModelAppliesTo | Unset
        if isinstance(_applies_to, Unset):
            applies_to = UNSET
        else:
            applies_to = DiscountModelAppliesTo.from_dict(_applies_to)

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

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        discount_model = cls(
            tenant_id=tenant_id,
            type_=type_,
            value=value,
            valid_from=valid_from,
            valid_until=valid_until,
            id=id,
            code=code,
            status=status,
            usage_limit=usage_limit,
            usage_count=usage_count,
            min_cart_value=min_cart_value,
            applies_to=applies_to,
            applies_to_flat=applies_to_flat,
            created_at=created_at,
            updated_at=updated_at,
        )

        discount_model.additional_properties = d
        return discount_model

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

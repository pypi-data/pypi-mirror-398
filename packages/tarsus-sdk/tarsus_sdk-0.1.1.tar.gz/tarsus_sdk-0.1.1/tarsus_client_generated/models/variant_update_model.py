from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant_update_model_options_type_0 import (
        VariantUpdateModelOptionsType0,
    )


T = TypeVar("T", bound="VariantUpdateModel")


@_attrs_define
class VariantUpdateModel:
    """Model for updating variants

    Attributes:
        sku (None | str | Unset):
        price (float | None | Unset):
        stock_quantity (int | None | Unset):
        options (None | Unset | VariantUpdateModelOptionsType0):
        image_url (None | str | Unset):
        is_active (bool | None | Unset):
        is_digital (bool | None | Unset):
        storage_path (None | str | Unset):
        modified_at (datetime.datetime | None | Unset):
    """

    sku: None | str | Unset = UNSET
    price: float | None | Unset = UNSET
    stock_quantity: int | None | Unset = UNSET
    options: None | Unset | VariantUpdateModelOptionsType0 = UNSET
    image_url: None | str | Unset = UNSET
    is_active: bool | None | Unset = UNSET
    is_digital: bool | None | Unset = UNSET
    storage_path: None | str | Unset = UNSET
    modified_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.variant_update_model_options_type_0 import (
            VariantUpdateModelOptionsType0,
        )

        sku: None | str | Unset
        if isinstance(self.sku, Unset):
            sku = UNSET
        else:
            sku = self.sku

        price: float | None | Unset
        if isinstance(self.price, Unset):
            price = UNSET
        else:
            price = self.price

        stock_quantity: int | None | Unset
        if isinstance(self.stock_quantity, Unset):
            stock_quantity = UNSET
        else:
            stock_quantity = self.stock_quantity

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, VariantUpdateModelOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        image_url: None | str | Unset
        if isinstance(self.image_url, Unset):
            image_url = UNSET
        else:
            image_url = self.image_url

        is_active: bool | None | Unset
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        is_digital: bool | None | Unset
        if isinstance(self.is_digital, Unset):
            is_digital = UNSET
        else:
            is_digital = self.is_digital

        storage_path: None | str | Unset
        if isinstance(self.storage_path, Unset):
            storage_path = UNSET
        else:
            storage_path = self.storage_path

        modified_at: None | str | Unset
        if isinstance(self.modified_at, Unset):
            modified_at = UNSET
        elif isinstance(self.modified_at, datetime.datetime):
            modified_at = self.modified_at.isoformat()
        else:
            modified_at = self.modified_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if sku is not UNSET:
            field_dict["sku"] = sku
        if price is not UNSET:
            field_dict["price"] = price
        if stock_quantity is not UNSET:
            field_dict["stock_quantity"] = stock_quantity
        if options is not UNSET:
            field_dict["options"] = options
        if image_url is not UNSET:
            field_dict["image_url"] = image_url
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if is_digital is not UNSET:
            field_dict["is_digital"] = is_digital
        if storage_path is not UNSET:
            field_dict["storage_path"] = storage_path
        if modified_at is not UNSET:
            field_dict["modified_at"] = modified_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.variant_update_model_options_type_0 import (
            VariantUpdateModelOptionsType0,
        )

        d = dict(src_dict)

        def _parse_sku(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sku = _parse_sku(d.pop("sku", UNSET))

        def _parse_price(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        price = _parse_price(d.pop("price", UNSET))

        def _parse_stock_quantity(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stock_quantity = _parse_stock_quantity(d.pop("stock_quantity", UNSET))

        def _parse_options(
            data: object,
        ) -> None | Unset | VariantUpdateModelOptionsType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = VariantUpdateModelOptionsType0.from_dict(data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | VariantUpdateModelOptionsType0, data)

        options = _parse_options(d.pop("options", UNSET))

        def _parse_image_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        image_url = _parse_image_url(d.pop("image_url", UNSET))

        def _parse_is_active(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        def _parse_is_digital(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_digital = _parse_is_digital(d.pop("is_digital", UNSET))

        def _parse_storage_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_path = _parse_storage_path(d.pop("storage_path", UNSET))

        def _parse_modified_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modified_at_type_0 = isoparse(data)

                return modified_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        modified_at = _parse_modified_at(d.pop("modified_at", UNSET))

        variant_update_model = cls(
            sku=sku,
            price=price,
            stock_quantity=stock_quantity,
            options=options,
            image_url=image_url,
            is_active=is_active,
            is_digital=is_digital,
            storage_path=storage_path,
            modified_at=modified_at,
        )

        variant_update_model.additional_properties = d
        return variant_update_model

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

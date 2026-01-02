from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant_model_options import VariantModelOptions


T = TypeVar("T", bound="VariantModel")


@_attrs_define
class VariantModel:
    """Individual SKU variant - the purchasable entity

    Attributes:
        sku (str):
        price (float):
        stock_quantity (int):
        options (VariantModelOptions):
        id (None | str | Unset):
        image_url (None | str | Unset):
        is_active (bool | Unset):  Default: True.
        is_digital (bool | Unset):  Default: False.
        storage_path (None | str | Unset):
        created_at (datetime.datetime | Unset):
        modified_at (datetime.datetime | None | Unset):
    """

    sku: str
    price: float
    stock_quantity: int
    options: VariantModelOptions
    id: None | str | Unset = UNSET
    image_url: None | str | Unset = UNSET
    is_active: bool | Unset = True
    is_digital: bool | Unset = False
    storage_path: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    modified_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sku = self.sku

        price = self.price

        stock_quantity = self.stock_quantity

        options = self.options.to_dict()

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        image_url: None | str | Unset
        if isinstance(self.image_url, Unset):
            image_url = UNSET
        else:
            image_url = self.image_url

        is_active = self.is_active

        is_digital = self.is_digital

        storage_path: None | str | Unset
        if isinstance(self.storage_path, Unset):
            storage_path = UNSET
        else:
            storage_path = self.storage_path

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        modified_at: None | str | Unset
        if isinstance(self.modified_at, Unset):
            modified_at = UNSET
        elif isinstance(self.modified_at, datetime.datetime):
            modified_at = self.modified_at.isoformat()
        else:
            modified_at = self.modified_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sku": sku,
                "price": price,
                "stock_quantity": stock_quantity,
                "options": options,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if image_url is not UNSET:
            field_dict["image_url"] = image_url
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if is_digital is not UNSET:
            field_dict["is_digital"] = is_digital
        if storage_path is not UNSET:
            field_dict["storage_path"] = storage_path
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if modified_at is not UNSET:
            field_dict["modified_at"] = modified_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.variant_model_options import VariantModelOptions

        d = dict(src_dict)
        sku = d.pop("sku")

        price = d.pop("price")

        stock_quantity = d.pop("stock_quantity")

        options = VariantModelOptions.from_dict(d.pop("options"))

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_image_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        image_url = _parse_image_url(d.pop("image_url", UNSET))

        is_active = d.pop("is_active", UNSET)

        is_digital = d.pop("is_digital", UNSET)

        def _parse_storage_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_path = _parse_storage_path(d.pop("storage_path", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

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

        variant_model = cls(
            sku=sku,
            price=price,
            stock_quantity=stock_quantity,
            options=options,
            id=id,
            image_url=image_url,
            is_active=is_active,
            is_digital=is_digital,
            storage_path=storage_path,
            created_at=created_at,
            modified_at=modified_at,
        )

        variant_model.additional_properties = d
        return variant_model

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

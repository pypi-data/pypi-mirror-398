from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="CategoryModel")


@_attrs_define
class CategoryModel:
    """Pydantic model for a product category.

    Attributes:
        name (str):
        id (None | str | Unset):
        description (None | str | Unset):
        parent_id (None | str | Unset):
        image_url (None | str | Unset):
        created_at (datetime.datetime | Unset):
        modified_at (datetime.datetime | None | Unset):
        is_active (bool | Unset):  Default: True.
        product_count (int | None | Unset):
    """

    name: str
    id: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    parent_id: None | str | Unset = UNSET
    image_url: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    modified_at: datetime.datetime | None | Unset = UNSET
    is_active: bool | Unset = True
    product_count: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        parent_id: None | str | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = self.parent_id

        image_url: None | str | Unset
        if isinstance(self.image_url, Unset):
            image_url = UNSET
        else:
            image_url = self.image_url

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

        is_active = self.is_active

        product_count: int | None | Unset
        if isinstance(self.product_count, Unset):
            product_count = UNSET
        else:
            product_count = self.product_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if description is not UNSET:
            field_dict["description"] = description
        if parent_id is not UNSET:
            field_dict["parent_id"] = parent_id
        if image_url is not UNSET:
            field_dict["image_url"] = image_url
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if modified_at is not UNSET:
            field_dict["modified_at"] = modified_at
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if product_count is not UNSET:
            field_dict["product_count"] = product_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_parent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_id = _parse_parent_id(d.pop("parent_id", UNSET))

        def _parse_image_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        image_url = _parse_image_url(d.pop("image_url", UNSET))

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

        is_active = d.pop("is_active", UNSET)

        def _parse_product_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        product_count = _parse_product_count(d.pop("product_count", UNSET))

        category_model = cls(
            name=name,
            id=id,
            description=description,
            parent_id=parent_id,
            image_url=image_url,
            created_at=created_at,
            modified_at=modified_at,
            is_active=is_active,
            product_count=product_count,
        )

        category_model.additional_properties = d
        return category_model

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

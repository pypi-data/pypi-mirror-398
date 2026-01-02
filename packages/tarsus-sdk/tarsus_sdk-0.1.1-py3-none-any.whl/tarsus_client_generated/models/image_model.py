from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.image_model_image_metadata_type_0 import ImageModelImageMetadataType0


T = TypeVar("T", bound="ImageModel")


@_attrs_define
class ImageModel:
    """Product image model

    Attributes:
        image_url (str):
        image_priority (int | Unset):  Default: 0.
        tag (None | str | Unset):
        product_item_number (None | str | Unset):
        image_metadata (ImageModelImageMetadataType0 | None | Unset):
        image_size (list[int] | None | Unset):
    """

    image_url: str
    image_priority: int | Unset = 0
    tag: None | str | Unset = UNSET
    product_item_number: None | str | Unset = UNSET
    image_metadata: ImageModelImageMetadataType0 | None | Unset = UNSET
    image_size: list[int] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.image_model_image_metadata_type_0 import (
            ImageModelImageMetadataType0,
        )

        image_url = self.image_url

        image_priority = self.image_priority

        tag: None | str | Unset
        if isinstance(self.tag, Unset):
            tag = UNSET
        else:
            tag = self.tag

        product_item_number: None | str | Unset
        if isinstance(self.product_item_number, Unset):
            product_item_number = UNSET
        else:
            product_item_number = self.product_item_number

        image_metadata: dict[str, Any] | None | Unset
        if isinstance(self.image_metadata, Unset):
            image_metadata = UNSET
        elif isinstance(self.image_metadata, ImageModelImageMetadataType0):
            image_metadata = self.image_metadata.to_dict()
        else:
            image_metadata = self.image_metadata

        image_size: list[int] | None | Unset
        if isinstance(self.image_size, Unset):
            image_size = UNSET
        elif isinstance(self.image_size, list):
            image_size = self.image_size

        else:
            image_size = self.image_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_url": image_url,
            }
        )
        if image_priority is not UNSET:
            field_dict["image_priority"] = image_priority
        if tag is not UNSET:
            field_dict["tag"] = tag
        if product_item_number is not UNSET:
            field_dict["product_item_number"] = product_item_number
        if image_metadata is not UNSET:
            field_dict["image_metadata"] = image_metadata
        if image_size is not UNSET:
            field_dict["image_size"] = image_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.image_model_image_metadata_type_0 import (
            ImageModelImageMetadataType0,
        )

        d = dict(src_dict)
        image_url = d.pop("image_url")

        image_priority = d.pop("image_priority", UNSET)

        def _parse_tag(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tag = _parse_tag(d.pop("tag", UNSET))

        def _parse_product_item_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        product_item_number = _parse_product_item_number(d.pop("product_item_number", UNSET))

        def _parse_image_metadata(
            data: object,
        ) -> ImageModelImageMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                image_metadata_type_0 = ImageModelImageMetadataType0.from_dict(data)

                return image_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ImageModelImageMetadataType0 | None | Unset, data)

        image_metadata = _parse_image_metadata(d.pop("image_metadata", UNSET))

        def _parse_image_size(data: object) -> list[int] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                image_size_type_0 = cast(list[int], data)

                return image_size_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | None | Unset, data)

        image_size = _parse_image_size(d.pop("image_size", UNSET))

        image_model = cls(
            image_url=image_url,
            image_priority=image_priority,
            tag=tag,
            product_item_number=product_item_number,
            image_metadata=image_metadata,
            image_size=image_size,
        )

        image_model.additional_properties = d
        return image_model

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

from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.product_type import ProductType
from ..models.service_billing_type import ServiceBillingType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.image_model import ImageModel
    from ..models.product_update_input_dimensions_type_0 import ProductUpdateInputDimensionsType0
    from ..models.product_update_input_metadata_type_0 import ProductUpdateInputMetadataType0
    from ..models.product_update_input_package_dimensions_type_0 import ProductUpdateInputPackageDimensionsType0


T = TypeVar("T", bound="ProductUpdateInput")


@_attrs_define
class ProductUpdateInput:
    """Input model for updating a product, including stock and storage handling

    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        base_price (float | None | Unset):
        images (list[ImageModel] | None | Unset):
        category (None | str | Unset):
        subcategory (None | str | Unset): Optional subcategory associated with the category
        product_type (None | ProductType | Unset):
        digital_product_access_url (None | str | Unset): URL or path to access/download digital product
        service_billing_type (None | ServiceBillingType | Unset):
        is_active (bool | None | Unset):
        item_number (None | str | Unset):
        dimensions (None | ProductUpdateInputDimensionsType0 | Unset):
        weight (float | None | Unset):
        package_dimensions (None | ProductUpdateInputPackageDimensionsType0 | Unset):
        materials (list[str] | None | Unset):
        manufacturer (None | str | Unset):
        metadata (None | ProductUpdateInputMetadataType0 | Unset):
        search_keywords (list[str] | None | Unset):
        tags (list[str] | None | Unset):
        modified_at (datetime.datetime | None | Unset):
        stock (int | None | Unset): Update stock quantity
        storage_path (None | str | Unset): Update storage path for digital products
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    base_price: float | None | Unset = UNSET
    images: list[ImageModel] | None | Unset = UNSET
    category: None | str | Unset = UNSET
    subcategory: None | str | Unset = UNSET
    product_type: None | ProductType | Unset = UNSET
    digital_product_access_url: None | str | Unset = UNSET
    service_billing_type: None | ServiceBillingType | Unset = UNSET
    is_active: bool | None | Unset = UNSET
    item_number: None | str | Unset = UNSET
    dimensions: None | ProductUpdateInputDimensionsType0 | Unset = UNSET
    weight: float | None | Unset = UNSET
    package_dimensions: None | ProductUpdateInputPackageDimensionsType0 | Unset = UNSET
    materials: list[str] | None | Unset = UNSET
    manufacturer: None | str | Unset = UNSET
    metadata: None | ProductUpdateInputMetadataType0 | Unset = UNSET
    search_keywords: list[str] | None | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    modified_at: datetime.datetime | None | Unset = UNSET
    stock: int | None | Unset = UNSET
    storage_path: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.product_update_input_dimensions_type_0 import ProductUpdateInputDimensionsType0
        from ..models.product_update_input_metadata_type_0 import ProductUpdateInputMetadataType0
        from ..models.product_update_input_package_dimensions_type_0 import ProductUpdateInputPackageDimensionsType0

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        base_price: float | None | Unset
        if isinstance(self.base_price, Unset):
            base_price = UNSET
        else:
            base_price = self.base_price

        images: list[dict[str, Any]] | None | Unset
        if isinstance(self.images, Unset):
            images = UNSET
        elif isinstance(self.images, list):
            images = []
            for images_type_0_item_data in self.images:
                images_type_0_item = images_type_0_item_data.to_dict()
                images.append(images_type_0_item)

        else:
            images = self.images

        category: None | str | Unset
        if isinstance(self.category, Unset):
            category = UNSET
        else:
            category = self.category

        subcategory: None | str | Unset
        if isinstance(self.subcategory, Unset):
            subcategory = UNSET
        else:
            subcategory = self.subcategory

        product_type: None | str | Unset
        if isinstance(self.product_type, Unset):
            product_type = UNSET
        elif isinstance(self.product_type, ProductType):
            product_type = self.product_type.value
        else:
            product_type = self.product_type

        digital_product_access_url: None | str | Unset
        if isinstance(self.digital_product_access_url, Unset):
            digital_product_access_url = UNSET
        else:
            digital_product_access_url = self.digital_product_access_url

        service_billing_type: None | str | Unset
        if isinstance(self.service_billing_type, Unset):
            service_billing_type = UNSET
        elif isinstance(self.service_billing_type, ServiceBillingType):
            service_billing_type = self.service_billing_type.value
        else:
            service_billing_type = self.service_billing_type

        is_active: bool | None | Unset
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        item_number: None | str | Unset
        if isinstance(self.item_number, Unset):
            item_number = UNSET
        else:
            item_number = self.item_number

        dimensions: dict[str, Any] | None | Unset
        if isinstance(self.dimensions, Unset):
            dimensions = UNSET
        elif isinstance(self.dimensions, ProductUpdateInputDimensionsType0):
            dimensions = self.dimensions.to_dict()
        else:
            dimensions = self.dimensions

        weight: float | None | Unset
        if isinstance(self.weight, Unset):
            weight = UNSET
        else:
            weight = self.weight

        package_dimensions: dict[str, Any] | None | Unset
        if isinstance(self.package_dimensions, Unset):
            package_dimensions = UNSET
        elif isinstance(self.package_dimensions, ProductUpdateInputPackageDimensionsType0):
            package_dimensions = self.package_dimensions.to_dict()
        else:
            package_dimensions = self.package_dimensions

        materials: list[str] | None | Unset
        if isinstance(self.materials, Unset):
            materials = UNSET
        elif isinstance(self.materials, list):
            materials = self.materials

        else:
            materials = self.materials

        manufacturer: None | str | Unset
        if isinstance(self.manufacturer, Unset):
            manufacturer = UNSET
        else:
            manufacturer = self.manufacturer

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ProductUpdateInputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        search_keywords: list[str] | None | Unset
        if isinstance(self.search_keywords, Unset):
            search_keywords = UNSET
        elif isinstance(self.search_keywords, list):
            search_keywords = self.search_keywords

        else:
            search_keywords = self.search_keywords

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        modified_at: None | str | Unset
        if isinstance(self.modified_at, Unset):
            modified_at = UNSET
        elif isinstance(self.modified_at, datetime.datetime):
            modified_at = self.modified_at.isoformat()
        else:
            modified_at = self.modified_at

        stock: int | None | Unset
        if isinstance(self.stock, Unset):
            stock = UNSET
        else:
            stock = self.stock

        storage_path: None | str | Unset
        if isinstance(self.storage_path, Unset):
            storage_path = UNSET
        else:
            storage_path = self.storage_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if base_price is not UNSET:
            field_dict["base_price"] = base_price
        if images is not UNSET:
            field_dict["images"] = images
        if category is not UNSET:
            field_dict["category"] = category
        if subcategory is not UNSET:
            field_dict["subcategory"] = subcategory
        if product_type is not UNSET:
            field_dict["product_type"] = product_type
        if digital_product_access_url is not UNSET:
            field_dict["digital_product_access_url"] = digital_product_access_url
        if service_billing_type is not UNSET:
            field_dict["service_billing_type"] = service_billing_type
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if item_number is not UNSET:
            field_dict["item_number"] = item_number
        if dimensions is not UNSET:
            field_dict["dimensions"] = dimensions
        if weight is not UNSET:
            field_dict["weight"] = weight
        if package_dimensions is not UNSET:
            field_dict["package_dimensions"] = package_dimensions
        if materials is not UNSET:
            field_dict["materials"] = materials
        if manufacturer is not UNSET:
            field_dict["manufacturer"] = manufacturer
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if search_keywords is not UNSET:
            field_dict["search_keywords"] = search_keywords
        if tags is not UNSET:
            field_dict["tags"] = tags
        if modified_at is not UNSET:
            field_dict["modified_at"] = modified_at
        if stock is not UNSET:
            field_dict["stock"] = stock
        if storage_path is not UNSET:
            field_dict["storage_path"] = storage_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.image_model import ImageModel
        from ..models.product_update_input_dimensions_type_0 import ProductUpdateInputDimensionsType0
        from ..models.product_update_input_metadata_type_0 import ProductUpdateInputMetadataType0
        from ..models.product_update_input_package_dimensions_type_0 import ProductUpdateInputPackageDimensionsType0

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_base_price(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        base_price = _parse_base_price(d.pop("base_price", UNSET))

        def _parse_images(data: object) -> list[ImageModel] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                images_type_0 = []
                _images_type_0 = data
                for images_type_0_item_data in _images_type_0:
                    images_type_0_item = ImageModel.from_dict(images_type_0_item_data)

                    images_type_0.append(images_type_0_item)

                return images_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ImageModel] | None | Unset, data)

        images = _parse_images(d.pop("images", UNSET))

        def _parse_category(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_subcategory(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subcategory = _parse_subcategory(d.pop("subcategory", UNSET))

        def _parse_product_type(data: object) -> None | ProductType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                product_type_type_0 = ProductType(data)

                return product_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductType | Unset, data)

        product_type = _parse_product_type(d.pop("product_type", UNSET))

        def _parse_digital_product_access_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        digital_product_access_url = _parse_digital_product_access_url(d.pop("digital_product_access_url", UNSET))

        def _parse_service_billing_type(data: object) -> None | ServiceBillingType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                service_billing_type_type_0 = ServiceBillingType(data)

                return service_billing_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ServiceBillingType | Unset, data)

        service_billing_type = _parse_service_billing_type(d.pop("service_billing_type", UNSET))

        def _parse_is_active(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        def _parse_item_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        item_number = _parse_item_number(d.pop("item_number", UNSET))

        def _parse_dimensions(data: object) -> None | ProductUpdateInputDimensionsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                dimensions_type_0 = ProductUpdateInputDimensionsType0.from_dict(data)

                return dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductUpdateInputDimensionsType0 | Unset, data)

        dimensions = _parse_dimensions(d.pop("dimensions", UNSET))

        def _parse_weight(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        weight = _parse_weight(d.pop("weight", UNSET))

        def _parse_package_dimensions(data: object) -> None | ProductUpdateInputPackageDimensionsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                package_dimensions_type_0 = ProductUpdateInputPackageDimensionsType0.from_dict(data)

                return package_dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductUpdateInputPackageDimensionsType0 | Unset, data)

        package_dimensions = _parse_package_dimensions(d.pop("package_dimensions", UNSET))

        def _parse_materials(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                materials_type_0 = cast(list[str], data)

                return materials_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        materials = _parse_materials(d.pop("materials", UNSET))

        def _parse_manufacturer(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        manufacturer = _parse_manufacturer(d.pop("manufacturer", UNSET))

        def _parse_metadata(data: object) -> None | ProductUpdateInputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ProductUpdateInputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductUpdateInputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_search_keywords(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                search_keywords_type_0 = cast(list[str], data)

                return search_keywords_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        search_keywords = _parse_search_keywords(d.pop("search_keywords", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

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

        def _parse_stock(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stock = _parse_stock(d.pop("stock", UNSET))

        def _parse_storage_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        storage_path = _parse_storage_path(d.pop("storage_path", UNSET))

        product_update_input = cls(
            name=name,
            description=description,
            base_price=base_price,
            images=images,
            category=category,
            subcategory=subcategory,
            product_type=product_type,
            digital_product_access_url=digital_product_access_url,
            service_billing_type=service_billing_type,
            is_active=is_active,
            item_number=item_number,
            dimensions=dimensions,
            weight=weight,
            package_dimensions=package_dimensions,
            materials=materials,
            manufacturer=manufacturer,
            metadata=metadata,
            search_keywords=search_keywords,
            tags=tags,
            modified_at=modified_at,
            stock=stock,
            storage_path=storage_path,
        )

        product_update_input.additional_properties = d
        return product_update_input

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

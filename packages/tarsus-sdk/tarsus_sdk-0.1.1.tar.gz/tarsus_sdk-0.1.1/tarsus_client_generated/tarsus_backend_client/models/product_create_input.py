from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.product_type import ProductType
from ..models.service_billing_type import ServiceBillingType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.image_model import ImageModel
    from ..models.product_create_input_bundle_components_type_0_item import ProductCreateInputBundleComponentsType0Item
    from ..models.product_create_input_dimensions_type_0 import ProductCreateInputDimensionsType0
    from ..models.product_create_input_metadata_type_0 import ProductCreateInputMetadataType0
    from ..models.product_create_input_options import ProductCreateInputOptions
    from ..models.product_create_input_package_dimensions_type_0 import ProductCreateInputPackageDimensionsType0


T = TypeVar("T", bound="ProductCreateInput")


@_attrs_define
class ProductCreateInput:
    """Input model for creating a product

    Attributes:
        name (str):
        description (str):
        base_price (float):
        category (str):
        images (list[ImageModel] | Unset):
        subcategory (None | str | Unset): Optional subcategory associated with the category
        product_type (ProductType | Unset):
        digital_product_access_url (None | str | Unset): URL or path to access/download digital product
        service_billing_type (None | ServiceBillingType | Unset): Billing type for service products: one_time or
            recurring
        is_active (bool | Unset):  Default: True.
        stock (int | None | Unset): Initial stock quantity for default availability Default: 0.
        storage_path (None | str | Unset): Storage path for digital product files
        options (ProductCreateInputOptions | Unset):
        available_colors (list[str] | Unset):
        available_sizes (list[str] | Unset):
        search_keywords (list[str] | Unset):
        tags (list[str] | Unset):
        item_number (None | str | Unset):
        sku (None | str | Unset):
        dimensions (None | ProductCreateInputDimensionsType0 | Unset):
        weight (float | None | Unset):
        package_dimensions (None | ProductCreateInputPackageDimensionsType0 | Unset):
        materials (list[str] | None | Unset):
        manufacturer (None | str | Unset):
        metadata (None | ProductCreateInputMetadataType0 | Unset):
        upsell_product_ids (list[str] | Unset):
        cross_sell_product_ids (list[str] | Unset):
        related_product_ids (list[str] | Unset):
        is_bundle (bool | Unset):  Default: False.
        bundle_components (list[ProductCreateInputBundleComponentsType0Item] | None | Unset):
    """

    name: str
    description: str
    base_price: float
    category: str
    images: list[ImageModel] | Unset = UNSET
    subcategory: None | str | Unset = UNSET
    product_type: ProductType | Unset = UNSET
    digital_product_access_url: None | str | Unset = UNSET
    service_billing_type: None | ServiceBillingType | Unset = UNSET
    is_active: bool | Unset = True
    stock: int | None | Unset = 0
    storage_path: None | str | Unset = UNSET
    options: ProductCreateInputOptions | Unset = UNSET
    available_colors: list[str] | Unset = UNSET
    available_sizes: list[str] | Unset = UNSET
    search_keywords: list[str] | Unset = UNSET
    tags: list[str] | Unset = UNSET
    item_number: None | str | Unset = UNSET
    sku: None | str | Unset = UNSET
    dimensions: None | ProductCreateInputDimensionsType0 | Unset = UNSET
    weight: float | None | Unset = UNSET
    package_dimensions: None | ProductCreateInputPackageDimensionsType0 | Unset = UNSET
    materials: list[str] | None | Unset = UNSET
    manufacturer: None | str | Unset = UNSET
    metadata: None | ProductCreateInputMetadataType0 | Unset = UNSET
    upsell_product_ids: list[str] | Unset = UNSET
    cross_sell_product_ids: list[str] | Unset = UNSET
    related_product_ids: list[str] | Unset = UNSET
    is_bundle: bool | Unset = False
    bundle_components: list[ProductCreateInputBundleComponentsType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.product_create_input_dimensions_type_0 import ProductCreateInputDimensionsType0
        from ..models.product_create_input_metadata_type_0 import ProductCreateInputMetadataType0
        from ..models.product_create_input_package_dimensions_type_0 import ProductCreateInputPackageDimensionsType0

        name = self.name

        description = self.description

        base_price = self.base_price

        category = self.category

        images: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.images, Unset):
            images = []
            for images_item_data in self.images:
                images_item = images_item_data.to_dict()
                images.append(images_item)

        subcategory: None | str | Unset
        if isinstance(self.subcategory, Unset):
            subcategory = UNSET
        else:
            subcategory = self.subcategory

        product_type: str | Unset = UNSET
        if not isinstance(self.product_type, Unset):
            product_type = self.product_type.value

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

        is_active = self.is_active

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

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        available_colors: list[str] | Unset = UNSET
        if not isinstance(self.available_colors, Unset):
            available_colors = self.available_colors

        available_sizes: list[str] | Unset = UNSET
        if not isinstance(self.available_sizes, Unset):
            available_sizes = self.available_sizes

        search_keywords: list[str] | Unset = UNSET
        if not isinstance(self.search_keywords, Unset):
            search_keywords = self.search_keywords

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        item_number: None | str | Unset
        if isinstance(self.item_number, Unset):
            item_number = UNSET
        else:
            item_number = self.item_number

        sku: None | str | Unset
        if isinstance(self.sku, Unset):
            sku = UNSET
        else:
            sku = self.sku

        dimensions: dict[str, Any] | None | Unset
        if isinstance(self.dimensions, Unset):
            dimensions = UNSET
        elif isinstance(self.dimensions, ProductCreateInputDimensionsType0):
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
        elif isinstance(self.package_dimensions, ProductCreateInputPackageDimensionsType0):
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
        elif isinstance(self.metadata, ProductCreateInputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        upsell_product_ids: list[str] | Unset = UNSET
        if not isinstance(self.upsell_product_ids, Unset):
            upsell_product_ids = self.upsell_product_ids

        cross_sell_product_ids: list[str] | Unset = UNSET
        if not isinstance(self.cross_sell_product_ids, Unset):
            cross_sell_product_ids = self.cross_sell_product_ids

        related_product_ids: list[str] | Unset = UNSET
        if not isinstance(self.related_product_ids, Unset):
            related_product_ids = self.related_product_ids

        is_bundle = self.is_bundle

        bundle_components: list[dict[str, Any]] | None | Unset
        if isinstance(self.bundle_components, Unset):
            bundle_components = UNSET
        elif isinstance(self.bundle_components, list):
            bundle_components = []
            for bundle_components_type_0_item_data in self.bundle_components:
                bundle_components_type_0_item = bundle_components_type_0_item_data.to_dict()
                bundle_components.append(bundle_components_type_0_item)

        else:
            bundle_components = self.bundle_components

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "base_price": base_price,
                "category": category,
            }
        )
        if images is not UNSET:
            field_dict["images"] = images
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
        if stock is not UNSET:
            field_dict["stock"] = stock
        if storage_path is not UNSET:
            field_dict["storage_path"] = storage_path
        if options is not UNSET:
            field_dict["options"] = options
        if available_colors is not UNSET:
            field_dict["available_colors"] = available_colors
        if available_sizes is not UNSET:
            field_dict["available_sizes"] = available_sizes
        if search_keywords is not UNSET:
            field_dict["search_keywords"] = search_keywords
        if tags is not UNSET:
            field_dict["tags"] = tags
        if item_number is not UNSET:
            field_dict["item_number"] = item_number
        if sku is not UNSET:
            field_dict["sku"] = sku
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
        if upsell_product_ids is not UNSET:
            field_dict["upsell_product_ids"] = upsell_product_ids
        if cross_sell_product_ids is not UNSET:
            field_dict["cross_sell_product_ids"] = cross_sell_product_ids
        if related_product_ids is not UNSET:
            field_dict["related_product_ids"] = related_product_ids
        if is_bundle is not UNSET:
            field_dict["is_bundle"] = is_bundle
        if bundle_components is not UNSET:
            field_dict["bundle_components"] = bundle_components

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.image_model import ImageModel
        from ..models.product_create_input_bundle_components_type_0_item import (
            ProductCreateInputBundleComponentsType0Item,
        )
        from ..models.product_create_input_dimensions_type_0 import ProductCreateInputDimensionsType0
        from ..models.product_create_input_metadata_type_0 import ProductCreateInputMetadataType0
        from ..models.product_create_input_options import ProductCreateInputOptions
        from ..models.product_create_input_package_dimensions_type_0 import ProductCreateInputPackageDimensionsType0

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        base_price = d.pop("base_price")

        category = d.pop("category")

        _images = d.pop("images", UNSET)
        images: list[ImageModel] | Unset = UNSET
        if _images is not UNSET:
            images = []
            for images_item_data in _images:
                images_item = ImageModel.from_dict(images_item_data)

                images.append(images_item)

        def _parse_subcategory(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subcategory = _parse_subcategory(d.pop("subcategory", UNSET))

        _product_type = d.pop("product_type", UNSET)
        product_type: ProductType | Unset
        if isinstance(_product_type, Unset):
            product_type = UNSET
        else:
            product_type = ProductType(_product_type)

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

        is_active = d.pop("is_active", UNSET)

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

        _options = d.pop("options", UNSET)
        options: ProductCreateInputOptions | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = ProductCreateInputOptions.from_dict(_options)

        available_colors = cast(list[str], d.pop("available_colors", UNSET))

        available_sizes = cast(list[str], d.pop("available_sizes", UNSET))

        search_keywords = cast(list[str], d.pop("search_keywords", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        def _parse_item_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        item_number = _parse_item_number(d.pop("item_number", UNSET))

        def _parse_sku(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sku = _parse_sku(d.pop("sku", UNSET))

        def _parse_dimensions(data: object) -> None | ProductCreateInputDimensionsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                dimensions_type_0 = ProductCreateInputDimensionsType0.from_dict(data)

                return dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductCreateInputDimensionsType0 | Unset, data)

        dimensions = _parse_dimensions(d.pop("dimensions", UNSET))

        def _parse_weight(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        weight = _parse_weight(d.pop("weight", UNSET))

        def _parse_package_dimensions(data: object) -> None | ProductCreateInputPackageDimensionsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                package_dimensions_type_0 = ProductCreateInputPackageDimensionsType0.from_dict(data)

                return package_dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductCreateInputPackageDimensionsType0 | Unset, data)

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

        def _parse_metadata(data: object) -> None | ProductCreateInputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ProductCreateInputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductCreateInputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        upsell_product_ids = cast(list[str], d.pop("upsell_product_ids", UNSET))

        cross_sell_product_ids = cast(list[str], d.pop("cross_sell_product_ids", UNSET))

        related_product_ids = cast(list[str], d.pop("related_product_ids", UNSET))

        is_bundle = d.pop("is_bundle", UNSET)

        def _parse_bundle_components(data: object) -> list[ProductCreateInputBundleComponentsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bundle_components_type_0 = []
                _bundle_components_type_0 = data
                for bundle_components_type_0_item_data in _bundle_components_type_0:
                    bundle_components_type_0_item = ProductCreateInputBundleComponentsType0Item.from_dict(
                        bundle_components_type_0_item_data
                    )

                    bundle_components_type_0.append(bundle_components_type_0_item)

                return bundle_components_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ProductCreateInputBundleComponentsType0Item] | None | Unset, data)

        bundle_components = _parse_bundle_components(d.pop("bundle_components", UNSET))

        product_create_input = cls(
            name=name,
            description=description,
            base_price=base_price,
            category=category,
            images=images,
            subcategory=subcategory,
            product_type=product_type,
            digital_product_access_url=digital_product_access_url,
            service_billing_type=service_billing_type,
            is_active=is_active,
            stock=stock,
            storage_path=storage_path,
            options=options,
            available_colors=available_colors,
            available_sizes=available_sizes,
            search_keywords=search_keywords,
            tags=tags,
            item_number=item_number,
            sku=sku,
            dimensions=dimensions,
            weight=weight,
            package_dimensions=package_dimensions,
            materials=materials,
            manufacturer=manufacturer,
            metadata=metadata,
            upsell_product_ids=upsell_product_ids,
            cross_sell_product_ids=cross_sell_product_ids,
            related_product_ids=related_product_ids,
            is_bundle=is_bundle,
            bundle_components=bundle_components,
        )

        product_create_input.additional_properties = d
        return product_create_input

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

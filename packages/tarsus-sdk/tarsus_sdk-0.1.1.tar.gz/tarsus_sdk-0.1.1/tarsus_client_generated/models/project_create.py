from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.payment_type import PaymentType
from ..models.product_type import ProductType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectCreate")


@_attrs_define
class ProjectCreate:
    """Model for creating a new project.

    Attributes:
        name (str):
        domain (None | str | Unset):
        description (None | str | Unset):
        primary_product_type (None | ProductType | Unset): Primary product type selected at creation
        primary_payment_type (None | PaymentType | Unset): Primary payment type selected at creation
        enabled_product_types (list[ProductType] | None | Unset):
        enabled_payment_types (list[PaymentType] | None | Unset):
    """

    name: str
    domain: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    primary_product_type: None | ProductType | Unset = UNSET
    primary_payment_type: None | PaymentType | Unset = UNSET
    enabled_product_types: list[ProductType] | None | Unset = UNSET
    enabled_payment_types: list[PaymentType] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        domain: None | str | Unset
        if isinstance(self.domain, Unset):
            domain = UNSET
        else:
            domain = self.domain

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        primary_product_type: None | str | Unset
        if isinstance(self.primary_product_type, Unset):
            primary_product_type = UNSET
        elif isinstance(self.primary_product_type, ProductType):
            primary_product_type = self.primary_product_type.value
        else:
            primary_product_type = self.primary_product_type

        primary_payment_type: None | str | Unset
        if isinstance(self.primary_payment_type, Unset):
            primary_payment_type = UNSET
        elif isinstance(self.primary_payment_type, PaymentType):
            primary_payment_type = self.primary_payment_type.value
        else:
            primary_payment_type = self.primary_payment_type

        enabled_product_types: list[str] | None | Unset
        if isinstance(self.enabled_product_types, Unset):
            enabled_product_types = UNSET
        elif isinstance(self.enabled_product_types, list):
            enabled_product_types = []
            for enabled_product_types_type_0_item_data in self.enabled_product_types:
                enabled_product_types_type_0_item = enabled_product_types_type_0_item_data.value
                enabled_product_types.append(enabled_product_types_type_0_item)

        else:
            enabled_product_types = self.enabled_product_types

        enabled_payment_types: list[str] | None | Unset
        if isinstance(self.enabled_payment_types, Unset):
            enabled_payment_types = UNSET
        elif isinstance(self.enabled_payment_types, list):
            enabled_payment_types = []
            for enabled_payment_types_type_0_item_data in self.enabled_payment_types:
                enabled_payment_types_type_0_item = enabled_payment_types_type_0_item_data.value
                enabled_payment_types.append(enabled_payment_types_type_0_item)

        else:
            enabled_payment_types = self.enabled_payment_types

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if domain is not UNSET:
            field_dict["domain"] = domain
        if description is not UNSET:
            field_dict["description"] = description
        if primary_product_type is not UNSET:
            field_dict["primary_product_type"] = primary_product_type
        if primary_payment_type is not UNSET:
            field_dict["primary_payment_type"] = primary_payment_type
        if enabled_product_types is not UNSET:
            field_dict["enabled_product_types"] = enabled_product_types
        if enabled_payment_types is not UNSET:
            field_dict["enabled_payment_types"] = enabled_payment_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_domain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        domain = _parse_domain(d.pop("domain", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_primary_product_type(data: object) -> None | ProductType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                primary_product_type_type_0 = ProductType(data)

                return primary_product_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProductType | Unset, data)

        primary_product_type = _parse_primary_product_type(d.pop("primary_product_type", UNSET))

        def _parse_primary_payment_type(data: object) -> None | PaymentType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                primary_payment_type_type_0 = PaymentType(data)

                return primary_payment_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PaymentType | Unset, data)

        primary_payment_type = _parse_primary_payment_type(d.pop("primary_payment_type", UNSET))

        def _parse_enabled_product_types(
            data: object,
        ) -> list[ProductType] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                enabled_product_types_type_0 = []
                _enabled_product_types_type_0 = data
                for enabled_product_types_type_0_item_data in _enabled_product_types_type_0:
                    enabled_product_types_type_0_item = ProductType(enabled_product_types_type_0_item_data)

                    enabled_product_types_type_0.append(enabled_product_types_type_0_item)

                return enabled_product_types_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ProductType] | None | Unset, data)

        enabled_product_types = _parse_enabled_product_types(d.pop("enabled_product_types", UNSET))

        def _parse_enabled_payment_types(
            data: object,
        ) -> list[PaymentType] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                enabled_payment_types_type_0 = []
                _enabled_payment_types_type_0 = data
                for enabled_payment_types_type_0_item_data in _enabled_payment_types_type_0:
                    enabled_payment_types_type_0_item = PaymentType(enabled_payment_types_type_0_item_data)

                    enabled_payment_types_type_0.append(enabled_payment_types_type_0_item)

                return enabled_payment_types_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PaymentType] | None | Unset, data)

        enabled_payment_types = _parse_enabled_payment_types(d.pop("enabled_payment_types", UNSET))

        project_create = cls(
            name=name,
            domain=domain,
            description=description,
            primary_product_type=primary_product_type,
            primary_payment_type=primary_payment_type,
            enabled_product_types=enabled_product_types,
            enabled_payment_types=enabled_payment_types,
        )

        project_create.additional_properties = d
        return project_create

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

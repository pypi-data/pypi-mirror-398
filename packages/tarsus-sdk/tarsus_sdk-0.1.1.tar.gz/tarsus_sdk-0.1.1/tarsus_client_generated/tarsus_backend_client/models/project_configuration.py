from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.payment_type import PaymentType
from ..models.project_product_type import ProjectProductType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectConfiguration")


@_attrs_define
class ProjectConfiguration:
    """Project feature configuration

    Attributes:
        enabled_product_types (list[ProjectProductType] | Unset): List of enabled product types for this project
        enabled_payment_types (list[PaymentType] | Unset): List of enabled payment types for this project
        default_product_type (None | ProjectProductType | Unset): Default product type for new products (primary
            selection at creation) Default: ProjectProductType.STANDARD_PHYSICAL.
        default_payment_type (None | PaymentType | Unset): Default payment type for new products (primary selection at
            creation) Default: PaymentType.ONE_TIME.
    """

    enabled_product_types: list[ProjectProductType] | Unset = UNSET
    enabled_payment_types: list[PaymentType] | Unset = UNSET
    default_product_type: None | ProjectProductType | Unset = ProjectProductType.STANDARD_PHYSICAL
    default_payment_type: None | PaymentType | Unset = PaymentType.ONE_TIME
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled_product_types: list[str] | Unset = UNSET
        if not isinstance(self.enabled_product_types, Unset):
            enabled_product_types = []
            for enabled_product_types_item_data in self.enabled_product_types:
                enabled_product_types_item = enabled_product_types_item_data.value
                enabled_product_types.append(enabled_product_types_item)

        enabled_payment_types: list[str] | Unset = UNSET
        if not isinstance(self.enabled_payment_types, Unset):
            enabled_payment_types = []
            for enabled_payment_types_item_data in self.enabled_payment_types:
                enabled_payment_types_item = enabled_payment_types_item_data.value
                enabled_payment_types.append(enabled_payment_types_item)

        default_product_type: None | str | Unset
        if isinstance(self.default_product_type, Unset):
            default_product_type = UNSET
        elif isinstance(self.default_product_type, ProjectProductType):
            default_product_type = self.default_product_type.value
        else:
            default_product_type = self.default_product_type

        default_payment_type: None | str | Unset
        if isinstance(self.default_payment_type, Unset):
            default_payment_type = UNSET
        elif isinstance(self.default_payment_type, PaymentType):
            default_payment_type = self.default_payment_type.value
        else:
            default_payment_type = self.default_payment_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enabled_product_types is not UNSET:
            field_dict["enabled_product_types"] = enabled_product_types
        if enabled_payment_types is not UNSET:
            field_dict["enabled_payment_types"] = enabled_payment_types
        if default_product_type is not UNSET:
            field_dict["default_product_type"] = default_product_type
        if default_payment_type is not UNSET:
            field_dict["default_payment_type"] = default_payment_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _enabled_product_types = d.pop("enabled_product_types", UNSET)
        enabled_product_types: list[ProjectProductType] | Unset = UNSET
        if _enabled_product_types is not UNSET:
            enabled_product_types = []
            for enabled_product_types_item_data in _enabled_product_types:
                enabled_product_types_item = ProjectProductType(enabled_product_types_item_data)

                enabled_product_types.append(enabled_product_types_item)

        _enabled_payment_types = d.pop("enabled_payment_types", UNSET)
        enabled_payment_types: list[PaymentType] | Unset = UNSET
        if _enabled_payment_types is not UNSET:
            enabled_payment_types = []
            for enabled_payment_types_item_data in _enabled_payment_types:
                enabled_payment_types_item = PaymentType(enabled_payment_types_item_data)

                enabled_payment_types.append(enabled_payment_types_item)

        def _parse_default_product_type(data: object) -> None | ProjectProductType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                default_product_type_type_0 = ProjectProductType(data)

                return default_product_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectProductType | Unset, data)

        default_product_type = _parse_default_product_type(d.pop("default_product_type", UNSET))

        def _parse_default_payment_type(data: object) -> None | PaymentType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                default_payment_type_type_0 = PaymentType(data)

                return default_payment_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PaymentType | Unset, data)

        default_payment_type = _parse_default_payment_type(d.pop("default_payment_type", UNSET))

        project_configuration = cls(
            enabled_product_types=enabled_product_types,
            enabled_payment_types=enabled_payment_types,
            default_product_type=default_product_type,
            default_payment_type=default_payment_type,
        )

        project_configuration.additional_properties = d
        return project_configuration

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

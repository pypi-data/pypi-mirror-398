from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.selected_modification_model import SelectedModificationModel


T = TypeVar("T", bound="OrderItemModel")


@_attrs_define
class OrderItemModel:
    """Order line item with variant and modification support

    Attributes:
        product_id (str):
        variant_id (str):
        variant_options (str):
        quantity (int):
        product_name (str):
        variant_sku (str):
        unit_price (float):
        line_item_total (float):
        selected_modifications (list[SelectedModificationModel] | Unset):
        is_digital (bool | Unset):  Default: False.
        license_key (None | str | Unset):
    """

    product_id: str
    variant_id: str
    variant_options: str
    quantity: int
    product_name: str
    variant_sku: str
    unit_price: float
    line_item_total: float
    selected_modifications: list[SelectedModificationModel] | Unset = UNSET
    is_digital: bool | Unset = False
    license_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        product_id = self.product_id

        variant_id = self.variant_id

        variant_options = self.variant_options

        quantity = self.quantity

        product_name = self.product_name

        variant_sku = self.variant_sku

        unit_price = self.unit_price

        line_item_total = self.line_item_total

        selected_modifications: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.selected_modifications, Unset):
            selected_modifications = []
            for selected_modifications_item_data in self.selected_modifications:
                selected_modifications_item = selected_modifications_item_data.to_dict()
                selected_modifications.append(selected_modifications_item)

        is_digital = self.is_digital

        license_key: None | str | Unset
        if isinstance(self.license_key, Unset):
            license_key = UNSET
        else:
            license_key = self.license_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "product_id": product_id,
                "variant_id": variant_id,
                "variant_options": variant_options,
                "quantity": quantity,
                "product_name": product_name,
                "variant_sku": variant_sku,
                "unit_price": unit_price,
                "line_item_total": line_item_total,
            }
        )
        if selected_modifications is not UNSET:
            field_dict["selected_modifications"] = selected_modifications
        if is_digital is not UNSET:
            field_dict["is_digital"] = is_digital
        if license_key is not UNSET:
            field_dict["license_key"] = license_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.selected_modification_model import SelectedModificationModel

        d = dict(src_dict)
        product_id = d.pop("product_id")

        variant_id = d.pop("variant_id")

        variant_options = d.pop("variant_options")

        quantity = d.pop("quantity")

        product_name = d.pop("product_name")

        variant_sku = d.pop("variant_sku")

        unit_price = d.pop("unit_price")

        line_item_total = d.pop("line_item_total")

        _selected_modifications = d.pop("selected_modifications", UNSET)
        selected_modifications: list[SelectedModificationModel] | Unset = UNSET
        if _selected_modifications is not UNSET:
            selected_modifications = []
            for selected_modifications_item_data in _selected_modifications:
                selected_modifications_item = SelectedModificationModel.from_dict(selected_modifications_item_data)

                selected_modifications.append(selected_modifications_item)

        is_digital = d.pop("is_digital", UNSET)

        def _parse_license_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        license_key = _parse_license_key(d.pop("license_key", UNSET))

        order_item_model = cls(
            product_id=product_id,
            variant_id=variant_id,
            variant_options=variant_options,
            quantity=quantity,
            product_name=product_name,
            variant_sku=variant_sku,
            unit_price=unit_price,
            line_item_total=line_item_total,
            selected_modifications=selected_modifications,
            is_digital=is_digital,
            license_key=license_key,
        )

        order_item_model.additional_properties = d
        return order_item_model

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

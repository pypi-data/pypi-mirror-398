from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SelectedModificationModel")


@_attrs_define
class SelectedModificationModel:
    """User's selected modification value (stored in order)

    Attributes:
        modification_id (str):
        label (str):
        value (str):
        price_adjustment (float):
        price_type (str):
    """

    modification_id: str
    label: str
    value: str
    price_adjustment: float
    price_type: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        modification_id = self.modification_id

        label = self.label

        value = self.value

        price_adjustment = self.price_adjustment

        price_type = self.price_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "modification_id": modification_id,
                "label": label,
                "value": value,
                "price_adjustment": price_adjustment,
                "price_type": price_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        modification_id = d.pop("modification_id")

        label = d.pop("label")

        value = d.pop("value")

        price_adjustment = d.pop("price_adjustment")

        price_type = d.pop("price_type")

        selected_modification_model = cls(
            modification_id=modification_id,
            label=label,
            value=value,
            price_adjustment=price_adjustment,
            price_type=price_type,
        )

        selected_modification_model.additional_properties = d
        return selected_modification_model

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

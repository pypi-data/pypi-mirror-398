from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.modification_type import ModificationType
from ..models.price_type import PriceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.modification_update_model_rules_type_0 import (
        ModificationUpdateModelRulesType0,
    )


T = TypeVar("T", bound="ModificationUpdateModel")


@_attrs_define
class ModificationUpdateModel:
    """Model for updating modifications

    Attributes:
        label (None | str | Unset):
        type_ (ModificationType | None | Unset):
        price_adjustment (float | None | Unset):
        price_type (None | PriceType | Unset):
        rules (ModificationUpdateModelRulesType0 | None | Unset):
        is_active (bool | None | Unset):
    """

    label: None | str | Unset = UNSET
    type_: ModificationType | None | Unset = UNSET
    price_adjustment: float | None | Unset = UNSET
    price_type: None | PriceType | Unset = UNSET
    rules: ModificationUpdateModelRulesType0 | None | Unset = UNSET
    is_active: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.modification_update_model_rules_type_0 import (
            ModificationUpdateModelRulesType0,
        )

        label: None | str | Unset
        if isinstance(self.label, Unset):
            label = UNSET
        else:
            label = self.label

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, ModificationType):
            type_ = self.type_.value
        else:
            type_ = self.type_

        price_adjustment: float | None | Unset
        if isinstance(self.price_adjustment, Unset):
            price_adjustment = UNSET
        else:
            price_adjustment = self.price_adjustment

        price_type: None | str | Unset
        if isinstance(self.price_type, Unset):
            price_type = UNSET
        elif isinstance(self.price_type, PriceType):
            price_type = self.price_type.value
        else:
            price_type = self.price_type

        rules: dict[str, Any] | None | Unset
        if isinstance(self.rules, Unset):
            rules = UNSET
        elif isinstance(self.rules, ModificationUpdateModelRulesType0):
            rules = self.rules.to_dict()
        else:
            rules = self.rules

        is_active: bool | None | Unset
        if isinstance(self.is_active, Unset):
            is_active = UNSET
        else:
            is_active = self.is_active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if label is not UNSET:
            field_dict["label"] = label
        if type_ is not UNSET:
            field_dict["type"] = type_
        if price_adjustment is not UNSET:
            field_dict["price_adjustment"] = price_adjustment
        if price_type is not UNSET:
            field_dict["price_type"] = price_type
        if rules is not UNSET:
            field_dict["rules"] = rules
        if is_active is not UNSET:
            field_dict["is_active"] = is_active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.modification_update_model_rules_type_0 import (
            ModificationUpdateModelRulesType0,
        )

        d = dict(src_dict)

        def _parse_label(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        label = _parse_label(d.pop("label", UNSET))

        def _parse_type_(data: object) -> ModificationType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = ModificationType(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModificationType | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_price_adjustment(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        price_adjustment = _parse_price_adjustment(d.pop("price_adjustment", UNSET))

        def _parse_price_type(data: object) -> None | PriceType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                price_type_type_0 = PriceType(data)

                return price_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PriceType | Unset, data)

        price_type = _parse_price_type(d.pop("price_type", UNSET))

        def _parse_rules(
            data: object,
        ) -> ModificationUpdateModelRulesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                rules_type_0 = ModificationUpdateModelRulesType0.from_dict(data)

                return rules_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModificationUpdateModelRulesType0 | None | Unset, data)

        rules = _parse_rules(d.pop("rules", UNSET))

        def _parse_is_active(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_active = _parse_is_active(d.pop("is_active", UNSET))

        modification_update_model = cls(
            label=label,
            type_=type_,
            price_adjustment=price_adjustment,
            price_type=price_type,
            rules=rules,
            is_active=is_active,
        )

        modification_update_model.additional_properties = d
        return modification_update_model

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

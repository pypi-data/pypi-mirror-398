from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.modification_type import ModificationType
from ..models.price_type import PriceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.modification_definition_model_rules_type_0 import ModificationDefinitionModelRulesType0


T = TypeVar("T", bound="ModificationDefinitionModel")


@_attrs_define
class ModificationDefinitionModel:
    """Definition of an available modification for a product

    Attributes:
        label (str):
        type_ (ModificationType):
        id (None | str | Unset):
        price_adjustment (float | Unset):  Default: 0.0.
        price_type (PriceType | Unset):
        rules (ModificationDefinitionModelRulesType0 | None | Unset):
        is_active (bool | Unset):  Default: True.
        created_at (datetime.datetime | Unset):
    """

    label: str
    type_: ModificationType
    id: None | str | Unset = UNSET
    price_adjustment: float | Unset = 0.0
    price_type: PriceType | Unset = UNSET
    rules: ModificationDefinitionModelRulesType0 | None | Unset = UNSET
    is_active: bool | Unset = True
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.modification_definition_model_rules_type_0 import ModificationDefinitionModelRulesType0

        label = self.label

        type_ = self.type_.value

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        price_adjustment = self.price_adjustment

        price_type: str | Unset = UNSET
        if not isinstance(self.price_type, Unset):
            price_type = self.price_type.value

        rules: dict[str, Any] | None | Unset
        if isinstance(self.rules, Unset):
            rules = UNSET
        elif isinstance(self.rules, ModificationDefinitionModelRulesType0):
            rules = self.rules.to_dict()
        else:
            rules = self.rules

        is_active = self.is_active

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label": label,
                "type": type_,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if price_adjustment is not UNSET:
            field_dict["price_adjustment"] = price_adjustment
        if price_type is not UNSET:
            field_dict["price_type"] = price_type
        if rules is not UNSET:
            field_dict["rules"] = rules
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.modification_definition_model_rules_type_0 import ModificationDefinitionModelRulesType0

        d = dict(src_dict)
        label = d.pop("label")

        type_ = ModificationType(d.pop("type"))

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        price_adjustment = d.pop("price_adjustment", UNSET)

        _price_type = d.pop("price_type", UNSET)
        price_type: PriceType | Unset
        if isinstance(_price_type, Unset):
            price_type = UNSET
        else:
            price_type = PriceType(_price_type)

        def _parse_rules(data: object) -> ModificationDefinitionModelRulesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                rules_type_0 = ModificationDefinitionModelRulesType0.from_dict(data)

                return rules_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ModificationDefinitionModelRulesType0 | None | Unset, data)

        rules = _parse_rules(d.pop("rules", UNSET))

        is_active = d.pop("is_active", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        modification_definition_model = cls(
            label=label,
            type_=type_,
            id=id,
            price_adjustment=price_adjustment,
            price_type=price_type,
            rules=rules,
            is_active=is_active,
            created_at=created_at,
        )

        modification_definition_model.additional_properties = d
        return modification_definition_model

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

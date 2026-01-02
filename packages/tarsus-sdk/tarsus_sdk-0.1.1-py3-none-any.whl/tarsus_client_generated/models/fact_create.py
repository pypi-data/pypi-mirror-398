from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fact_create_metadata import FactCreateMetadata


T = TypeVar("T", bound="FactCreate")


@_attrs_define
class FactCreate:
    """Request model for creating a fact.

    Attributes:
        content (str): Fact content
        category (str): Category
        confidence (float | Unset):  Default: 1.0.
        metadata (FactCreateMetadata | Unset):
    """

    content: str
    category: str
    confidence: float | Unset = 1.0
    metadata: FactCreateMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        category = self.category

        confidence = self.confidence

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
                "category": category,
            }
        )
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fact_create_metadata import FactCreateMetadata

        d = dict(src_dict)
        content = d.pop("content")

        category = d.pop("category")

        confidence = d.pop("confidence", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: FactCreateMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = FactCreateMetadata.from_dict(_metadata)

        fact_create = cls(
            content=content,
            category=category,
            confidence=confidence,
            metadata=metadata,
        )

        fact_create.additional_properties = d
        return fact_create

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

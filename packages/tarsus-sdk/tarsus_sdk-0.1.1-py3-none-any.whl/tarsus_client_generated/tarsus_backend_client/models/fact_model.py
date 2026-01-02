from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fact_model_metadata import FactModelMetadata


T = TypeVar("T", bound="FactModel")


@_attrs_define
class FactModel:
    """Model for a structured fact (rule, constraint, decision).
    Stored in /artifacts/{tenant_id}/memory/facts/{fact_id}

        Attributes:
            tenant_id (str): Tenant ID
            content (str): The fact content (e.g., 'Users cannot delete orders')
            category (str): Category (e.g., 'security', 'architecture', 'business_rule')
            id (None | str | Unset): ULID of the fact
            confidence (float | Unset): Confidence score (0-1) Default: 1.0.
            metadata (FactModelMetadata | Unset): Additional metadata
            created_at (datetime.datetime | Unset):
            updated_at (datetime.datetime | None | Unset):
    """

    tenant_id: str
    content: str
    category: str
    id: None | str | Unset = UNSET
    confidence: float | Unset = 1.0
    metadata: FactModelMetadata | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        content = self.content

        category = self.category

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        confidence = self.confidence

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenant_id": tenant_id,
                "content": content,
                "category": category,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fact_model_metadata import FactModelMetadata

        d = dict(src_dict)
        tenant_id = d.pop("tenant_id")

        content = d.pop("content")

        category = d.pop("category")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        confidence = d.pop("confidence", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: FactModelMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = FactModelMetadata.from_dict(_metadata)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        def _parse_updated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        fact_model = cls(
            tenant_id=tenant_id,
            content=content,
            category=category,
            id=id,
            confidence=confidence,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
        )

        fact_model.additional_properties = d
        return fact_model

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

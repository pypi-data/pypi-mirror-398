from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.knowledge_chunk_create_metadata import KnowledgeChunkCreateMetadata


T = TypeVar("T", bound="KnowledgeChunkCreate")


@_attrs_define
class KnowledgeChunkCreate:
    """Request model for creating a knowledge chunk.

    Attributes:
        content (str): Text content to store
        source (None | str | Unset): Source identifier
        source_type (None | str | Unset): Type of source
        metadata (KnowledgeChunkCreateMetadata | Unset):
    """

    content: str
    source: None | str | Unset = UNSET
    source_type: None | str | Unset = UNSET
    metadata: KnowledgeChunkCreateMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        source_type: None | str | Unset
        if isinstance(self.source_type, Unset):
            source_type = UNSET
        else:
            source_type = self.source_type

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.knowledge_chunk_create_metadata import KnowledgeChunkCreateMetadata

        d = dict(src_dict)
        content = d.pop("content")

        def _parse_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        def _parse_source_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_type = _parse_source_type(d.pop("source_type", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: KnowledgeChunkCreateMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = KnowledgeChunkCreateMetadata.from_dict(_metadata)

        knowledge_chunk_create = cls(
            content=content,
            source=source,
            source_type=source_type,
            metadata=metadata,
        )

        knowledge_chunk_create.additional_properties = d
        return knowledge_chunk_create

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

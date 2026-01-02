from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.knowledge_chunk_model_metadata import KnowledgeChunkModelMetadata


T = TypeVar("T", bound="KnowledgeChunkModel")


@_attrs_define
class KnowledgeChunkModel:
    """Model for a knowledge chunk (text with embedding).
    Stored in /artifacts/{tenant_id}/memory/knowledge/{chunk_id}

        Attributes:
            tenant_id (str): Tenant ID
            content (str): The text content of the chunk
            id (None | str | Unset): ULID of the chunk
            source (None | str | Unset): Source of the content (e.g., filename, URL)
            source_type (None | str | Unset): Type of source (e.g., 'pdf', 'markdown', 'text')
            metadata (KnowledgeChunkModelMetadata | Unset): Additional metadata
            embedding (list[float] | None | Unset): Vector embedding (768 dimensions)
            chunk_index (int | None | Unset): Index of this chunk in the source document
            created_at (datetime.datetime | Unset):
    """

    tenant_id: str
    content: str
    id: None | str | Unset = UNSET
    source: None | str | Unset = UNSET
    source_type: None | str | Unset = UNSET
    metadata: KnowledgeChunkModelMetadata | Unset = UNSET
    embedding: list[float] | None | Unset = UNSET
    chunk_index: int | None | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tenant_id = self.tenant_id

        content = self.content

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

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

        embedding: list[float] | None | Unset
        if isinstance(self.embedding, Unset):
            embedding = UNSET
        elif isinstance(self.embedding, list):
            embedding = self.embedding

        else:
            embedding = self.embedding

        chunk_index: int | None | Unset
        if isinstance(self.chunk_index, Unset):
            chunk_index = UNSET
        else:
            chunk_index = self.chunk_index

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenant_id": tenant_id,
                "content": content,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if source is not UNSET:
            field_dict["source"] = source
        if source_type is not UNSET:
            field_dict["source_type"] = source_type
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if embedding is not UNSET:
            field_dict["embedding"] = embedding
        if chunk_index is not UNSET:
            field_dict["chunk_index"] = chunk_index
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.knowledge_chunk_model_metadata import KnowledgeChunkModelMetadata

        d = dict(src_dict)
        tenant_id = d.pop("tenant_id")

        content = d.pop("content")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

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
        metadata: KnowledgeChunkModelMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = KnowledgeChunkModelMetadata.from_dict(_metadata)

        def _parse_embedding(data: object) -> list[float] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                embedding_type_0 = cast(list[float], data)

                return embedding_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[float] | None | Unset, data)

        embedding = _parse_embedding(d.pop("embedding", UNSET))

        def _parse_chunk_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        chunk_index = _parse_chunk_index(d.pop("chunk_index", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        knowledge_chunk_model = cls(
            tenant_id=tenant_id,
            content=content,
            id=id,
            source=source,
            source_type=source_type,
            metadata=metadata,
            embedding=embedding,
            chunk_index=chunk_index,
            created_at=created_at,
        )

        knowledge_chunk_model.additional_properties = d
        return knowledge_chunk_model

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

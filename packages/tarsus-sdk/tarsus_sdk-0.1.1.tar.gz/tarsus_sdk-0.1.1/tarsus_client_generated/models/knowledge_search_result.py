from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.knowledge_chunk_model import KnowledgeChunkModel


T = TypeVar("T", bound="KnowledgeSearchResult")


@_attrs_define
class KnowledgeSearchResult:
    """Result model for knowledge search.

    Attributes:
        chunk (KnowledgeChunkModel): Model for a knowledge chunk (text with embedding).
            Stored in /artifacts/{tenant_id}/memory/knowledge/{chunk_id}
        score (float): Similarity score (0-1)
    """

    chunk: KnowledgeChunkModel
    score: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        chunk = self.chunk.to_dict()

        score = self.score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "chunk": chunk,
                "score": score,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.knowledge_chunk_model import KnowledgeChunkModel

        d = dict(src_dict)
        chunk = KnowledgeChunkModel.from_dict(d.pop("chunk"))

        score = d.pop("score")

        knowledge_search_result = cls(
            chunk=chunk,
            score=score,
        )

        knowledge_search_result.additional_properties = d
        return knowledge_search_result

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

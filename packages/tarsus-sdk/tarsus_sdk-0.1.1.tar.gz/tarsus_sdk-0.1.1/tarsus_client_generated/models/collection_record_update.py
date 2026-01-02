from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.collection_record_update_data import CollectionRecordUpdateData


T = TypeVar("T", bound="CollectionRecordUpdate")


@_attrs_define
class CollectionRecordUpdate:
    """Request model for updating a record - only requires data

    Attributes:
        data (CollectionRecordUpdateData): Updated JSON data for this record
    """

    data: CollectionRecordUpdateData
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.collection_record_update_data import CollectionRecordUpdateData

        d = dict(src_dict)
        data = CollectionRecordUpdateData.from_dict(d.pop("data"))

        collection_record_update = cls(
            data=data,
        )

        collection_record_update.additional_properties = d
        return collection_record_update

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

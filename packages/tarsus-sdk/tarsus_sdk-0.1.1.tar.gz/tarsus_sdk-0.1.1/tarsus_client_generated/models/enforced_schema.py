from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.enforced_schema_schema_definition import (
        EnforcedSchemaSchemaDefinition,
    )
    from ..models.enforced_schema_validation_report_type_0 import (
        EnforcedSchemaValidationReportType0,
    )


T = TypeVar("T", bound="EnforcedSchema")


@_attrs_define
class EnforcedSchema:
    """Model for an enforced schema.
    Stored in /artifacts/{tenant_id}/_internal/enforced_schemas/{collection_name}

        Attributes:
            collection_name (str): Collection name
            tenant_id (str): Tenant ID
            schema_definition (EnforcedSchemaSchemaDefinition): JSON Schema definition
            enforced_at (datetime.datetime | Unset):
            enforced_by (None | str | Unset): User/agent that enforced the schema
            validation_report (EnforcedSchemaValidationReportType0 | None | Unset): Initial validation report
    """

    collection_name: str
    tenant_id: str
    schema_definition: EnforcedSchemaSchemaDefinition
    enforced_at: datetime.datetime | Unset = UNSET
    enforced_by: None | str | Unset = UNSET
    validation_report: EnforcedSchemaValidationReportType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.enforced_schema_validation_report_type_0 import (
            EnforcedSchemaValidationReportType0,
        )

        collection_name = self.collection_name

        tenant_id = self.tenant_id

        schema_definition = self.schema_definition.to_dict()

        enforced_at: str | Unset = UNSET
        if not isinstance(self.enforced_at, Unset):
            enforced_at = self.enforced_at.isoformat()

        enforced_by: None | str | Unset
        if isinstance(self.enforced_by, Unset):
            enforced_by = UNSET
        else:
            enforced_by = self.enforced_by

        validation_report: dict[str, Any] | None | Unset
        if isinstance(self.validation_report, Unset):
            validation_report = UNSET
        elif isinstance(self.validation_report, EnforcedSchemaValidationReportType0):
            validation_report = self.validation_report.to_dict()
        else:
            validation_report = self.validation_report

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "collection_name": collection_name,
                "tenant_id": tenant_id,
                "schema_definition": schema_definition,
            }
        )
        if enforced_at is not UNSET:
            field_dict["enforced_at"] = enforced_at
        if enforced_by is not UNSET:
            field_dict["enforced_by"] = enforced_by
        if validation_report is not UNSET:
            field_dict["validation_report"] = validation_report

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.enforced_schema_schema_definition import (
            EnforcedSchemaSchemaDefinition,
        )
        from ..models.enforced_schema_validation_report_type_0 import (
            EnforcedSchemaValidationReportType0,
        )

        d = dict(src_dict)
        collection_name = d.pop("collection_name")

        tenant_id = d.pop("tenant_id")

        schema_definition = EnforcedSchemaSchemaDefinition.from_dict(d.pop("schema_definition"))

        _enforced_at = d.pop("enforced_at", UNSET)
        enforced_at: datetime.datetime | Unset
        if isinstance(_enforced_at, Unset):
            enforced_at = UNSET
        else:
            enforced_at = isoparse(_enforced_at)

        def _parse_enforced_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        enforced_by = _parse_enforced_by(d.pop("enforced_by", UNSET))

        def _parse_validation_report(
            data: object,
        ) -> EnforcedSchemaValidationReportType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                validation_report_type_0 = EnforcedSchemaValidationReportType0.from_dict(data)

                return validation_report_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EnforcedSchemaValidationReportType0 | None | Unset, data)

        validation_report = _parse_validation_report(d.pop("validation_report", UNSET))

        enforced_schema = cls(
            collection_name=collection_name,
            tenant_id=tenant_id,
            schema_definition=schema_definition,
            enforced_at=enforced_at,
            enforced_by=enforced_by,
            validation_report=validation_report,
        )

        enforced_schema.additional_properties = d
        return enforced_schema

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

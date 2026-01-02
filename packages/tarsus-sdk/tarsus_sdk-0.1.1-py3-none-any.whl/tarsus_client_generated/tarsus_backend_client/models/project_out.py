from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.project_out_project_type import ProjectOutProjectType
from ..models.project_out_subscription_status_type_0 import ProjectOutSubscriptionStatusType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.allowed_origin import AllowedOrigin
    from ..models.project_configuration import ProjectConfiguration


T = TypeVar("T", bound="ProjectOut")


@_attrs_define
class ProjectOut:
    """Output model for project (simplified, no credentials).

    Attributes:
        id (None | str):
        backend_user_id (str):
        name (str):
        domain (None | str):
        description (None | str):
        easypost_configured (bool):
        stripe_configured (bool):
        is_active (bool):
        project_type (ProjectOutProjectType):
        created_at (datetime.datetime):
        updated_at (datetime.datetime | None):
        subscription_status (None | ProjectOutSubscriptionStatusType0 | Unset):
        is_pay_as_you_go (bool | Unset):  Default: False.
        allowed_origins (list[AllowedOrigin] | Unset):
        configuration (None | ProjectConfiguration | Unset):
        bucket_name (None | str | Unset):
    """

    id: None | str
    backend_user_id: str
    name: str
    domain: None | str
    description: None | str
    easypost_configured: bool
    stripe_configured: bool
    is_active: bool
    project_type: ProjectOutProjectType
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    subscription_status: None | ProjectOutSubscriptionStatusType0 | Unset = UNSET
    is_pay_as_you_go: bool | Unset = False
    allowed_origins: list[AllowedOrigin] | Unset = UNSET
    configuration: None | ProjectConfiguration | Unset = UNSET
    bucket_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.project_configuration import ProjectConfiguration

        id: None | str
        id = self.id

        backend_user_id = self.backend_user_id

        name = self.name

        domain: None | str
        domain = self.domain

        description: None | str
        description = self.description

        easypost_configured = self.easypost_configured

        stripe_configured = self.stripe_configured

        is_active = self.is_active

        project_type = self.project_type.value

        created_at = self.created_at.isoformat()

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        subscription_status: None | str | Unset
        if isinstance(self.subscription_status, Unset):
            subscription_status = UNSET
        elif isinstance(self.subscription_status, ProjectOutSubscriptionStatusType0):
            subscription_status = self.subscription_status.value
        else:
            subscription_status = self.subscription_status

        is_pay_as_you_go = self.is_pay_as_you_go

        allowed_origins: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.allowed_origins, Unset):
            allowed_origins = []
            for allowed_origins_item_data in self.allowed_origins:
                allowed_origins_item = allowed_origins_item_data.to_dict()
                allowed_origins.append(allowed_origins_item)

        configuration: dict[str, Any] | None | Unset
        if isinstance(self.configuration, Unset):
            configuration = UNSET
        elif isinstance(self.configuration, ProjectConfiguration):
            configuration = self.configuration.to_dict()
        else:
            configuration = self.configuration

        bucket_name: None | str | Unset
        if isinstance(self.bucket_name, Unset):
            bucket_name = UNSET
        else:
            bucket_name = self.bucket_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "backend_user_id": backend_user_id,
                "name": name,
                "domain": domain,
                "description": description,
                "easypost_configured": easypost_configured,
                "stripe_configured": stripe_configured,
                "is_active": is_active,
                "project_type": project_type,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if subscription_status is not UNSET:
            field_dict["subscription_status"] = subscription_status
        if is_pay_as_you_go is not UNSET:
            field_dict["is_pay_as_you_go"] = is_pay_as_you_go
        if allowed_origins is not UNSET:
            field_dict["allowed_origins"] = allowed_origins
        if configuration is not UNSET:
            field_dict["configuration"] = configuration
        if bucket_name is not UNSET:
            field_dict["bucket_name"] = bucket_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.allowed_origin import AllowedOrigin
        from ..models.project_configuration import ProjectConfiguration

        d = dict(src_dict)

        def _parse_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        id = _parse_id(d.pop("id"))

        backend_user_id = d.pop("backend_user_id")

        name = d.pop("name")

        def _parse_domain(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        domain = _parse_domain(d.pop("domain"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        easypost_configured = d.pop("easypost_configured")

        stripe_configured = d.pop("stripe_configured")

        is_active = d.pop("is_active")

        project_type = ProjectOutProjectType(d.pop("project_type"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_updated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at"))

        def _parse_subscription_status(data: object) -> None | ProjectOutSubscriptionStatusType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                subscription_status_type_0 = ProjectOutSubscriptionStatusType0(data)

                return subscription_status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectOutSubscriptionStatusType0 | Unset, data)

        subscription_status = _parse_subscription_status(d.pop("subscription_status", UNSET))

        is_pay_as_you_go = d.pop("is_pay_as_you_go", UNSET)

        _allowed_origins = d.pop("allowed_origins", UNSET)
        allowed_origins: list[AllowedOrigin] | Unset = UNSET
        if _allowed_origins is not UNSET:
            allowed_origins = []
            for allowed_origins_item_data in _allowed_origins:
                allowed_origins_item = AllowedOrigin.from_dict(allowed_origins_item_data)

                allowed_origins.append(allowed_origins_item)

        def _parse_configuration(data: object) -> None | ProjectConfiguration | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_0 = ProjectConfiguration.from_dict(data)

                return configuration_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectConfiguration | Unset, data)

        configuration = _parse_configuration(d.pop("configuration", UNSET))

        def _parse_bucket_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bucket_name = _parse_bucket_name(d.pop("bucket_name", UNSET))

        project_out = cls(
            id=id,
            backend_user_id=backend_user_id,
            name=name,
            domain=domain,
            description=description,
            easypost_configured=easypost_configured,
            stripe_configured=stripe_configured,
            is_active=is_active,
            project_type=project_type,
            created_at=created_at,
            updated_at=updated_at,
            subscription_status=subscription_status,
            is_pay_as_you_go=is_pay_as_you_go,
            allowed_origins=allowed_origins,
            configuration=configuration,
            bucket_name=bucket_name,
        )

        project_out.additional_properties = d
        return project_out

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

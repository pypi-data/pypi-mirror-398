from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.project_public_project_type import ProjectPublicProjectType
from ..models.project_public_subscription_status_type_0 import (
    ProjectPublicSubscriptionStatusType0,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.allowed_origin import AllowedOrigin
    from ..models.email_branding import EmailBranding
    from ..models.project_configuration import ProjectConfiguration


T = TypeVar("T", bound="ProjectPublic")


@_attrs_define
class ProjectPublic:
    """Public representation of a project (without sensitive credentials).

    Attributes:
        id (None | str):
        backend_user_id (str):
        name (str):
        domain (None | str):
        description (None | str):
        created_at (datetime.datetime):
        easypost_configured (bool | Unset):  Default: False.
        stripe_configured (bool | Unset):  Default: False.
        is_active (bool | Unset):  Default: True.
        project_type (ProjectPublicProjectType | Unset):  Default: ProjectPublicProjectType.FREE.
        subscription_status (None | ProjectPublicSubscriptionStatusType0 | Unset):
        is_pay_as_you_go (bool | Unset):  Default: False.
        allowed_origins (list[AllowedOrigin] | Unset):
        configuration (None | ProjectConfiguration | Unset):
        email_branding (EmailBranding | None | Unset):
        bucket_name (None | str | Unset):
        updated_at (datetime.datetime | None | Unset):
    """

    id: None | str
    backend_user_id: str
    name: str
    domain: None | str
    description: None | str
    created_at: datetime.datetime
    easypost_configured: bool | Unset = False
    stripe_configured: bool | Unset = False
    is_active: bool | Unset = True
    project_type: ProjectPublicProjectType | Unset = ProjectPublicProjectType.FREE
    subscription_status: None | ProjectPublicSubscriptionStatusType0 | Unset = UNSET
    is_pay_as_you_go: bool | Unset = False
    allowed_origins: list[AllowedOrigin] | Unset = UNSET
    configuration: None | ProjectConfiguration | Unset = UNSET
    email_branding: EmailBranding | None | Unset = UNSET
    bucket_name: None | str | Unset = UNSET
    updated_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.email_branding import EmailBranding
        from ..models.project_configuration import ProjectConfiguration

        id: None | str
        id = self.id

        backend_user_id = self.backend_user_id

        name = self.name

        domain: None | str
        domain = self.domain

        description: None | str
        description = self.description

        created_at = self.created_at.isoformat()

        easypost_configured = self.easypost_configured

        stripe_configured = self.stripe_configured

        is_active = self.is_active

        project_type: str | Unset = UNSET
        if not isinstance(self.project_type, Unset):
            project_type = self.project_type.value

        subscription_status: None | str | Unset
        if isinstance(self.subscription_status, Unset):
            subscription_status = UNSET
        elif isinstance(self.subscription_status, ProjectPublicSubscriptionStatusType0):
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

        email_branding: dict[str, Any] | None | Unset
        if isinstance(self.email_branding, Unset):
            email_branding = UNSET
        elif isinstance(self.email_branding, EmailBranding):
            email_branding = self.email_branding.to_dict()
        else:
            email_branding = self.email_branding

        bucket_name = self.bucket_name

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
                "id": id,
                "backend_user_id": backend_user_id,
                "name": name,
                "domain": domain,
                "description": description,
                "created_at": created_at,
            }
        )
        if easypost_configured is not UNSET:
            field_dict["easypost_configured"] = easypost_configured
        if stripe_configured is not UNSET:
            field_dict["stripe_configured"] = stripe_configured
        if is_active is not UNSET:
            field_dict["is_active"] = is_active
        if project_type is not UNSET:
            field_dict["project_type"] = project_type
        if subscription_status is not UNSET:
            field_dict["subscription_status"] = subscription_status
        if is_pay_as_you_go is not UNSET:
            field_dict["is_pay_as_you_go"] = is_pay_as_you_go
        if allowed_origins is not UNSET:
            field_dict["allowed_origins"] = allowed_origins
        if configuration is not UNSET:
            field_dict["configuration"] = configuration
        if email_branding is not UNSET:
            field_dict["email_branding"] = email_branding
        if bucket_name is not UNSET:
            field_dict["bucket_name"] = bucket_name
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.allowed_origin import AllowedOrigin
        from ..models.email_branding import EmailBranding
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

        created_at = isoparse(d.pop("created_at"))

        easypost_configured = d.pop("easypost_configured", UNSET)

        stripe_configured = d.pop("stripe_configured", UNSET)

        is_active = d.pop("is_active", UNSET)

        _project_type = d.pop("project_type", UNSET)
        project_type: ProjectPublicProjectType | Unset
        if isinstance(_project_type, Unset):
            project_type = UNSET
        else:
            project_type = ProjectPublicProjectType(_project_type)

        def _parse_subscription_status(
            data: object,
        ) -> None | ProjectPublicSubscriptionStatusType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                subscription_status_type_0 = ProjectPublicSubscriptionStatusType0(data)

                return subscription_status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectPublicSubscriptionStatusType0 | Unset, data)

        subscription_status = _parse_subscription_status(
            d.pop("subscription_status", UNSET)
        )

        is_pay_as_you_go = d.pop("is_pay_as_you_go", UNSET)

        _allowed_origins = d.pop("allowed_origins", UNSET)
        allowed_origins: list[AllowedOrigin] | Unset = UNSET
        if _allowed_origins is not UNSET:
            allowed_origins = []
            for allowed_origins_item_data in _allowed_origins:
                allowed_origins_item = AllowedOrigin.from_dict(
                    allowed_origins_item_data
                )

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

        def _parse_email_branding(data: object) -> EmailBranding | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                email_branding_type_0 = EmailBranding.from_dict(data)

                return email_branding_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EmailBranding | None | Unset, data)

        email_branding = _parse_email_branding(d.pop("email_branding", UNSET))

        def _parse_bucket_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bucket_name = _parse_bucket_name(d.pop("bucket_name", UNSET))

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

        project_public = cls(
            id=id,
            backend_user_id=backend_user_id,
            name=name,
            domain=domain,
            description=description,
            created_at=created_at,
            easypost_configured=easypost_configured,
            stripe_configured=stripe_configured,
            is_active=is_active,
            project_type=project_type,
            subscription_status=subscription_status,
            is_pay_as_you_go=is_pay_as_you_go,
            allowed_origins=allowed_origins,
            configuration=configuration,
            email_branding=email_branding,
            bucket_name=bucket_name,
            updated_at=updated_at,
        )

        project_public.additional_properties = d
        return project_public

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

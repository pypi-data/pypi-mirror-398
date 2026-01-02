from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.platform_key_status import PlatformKeyStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="PlatformKeyUpdate")


@_attrs_define
class PlatformKeyUpdate:
    """Model for updating a platform key

    Attributes:
        status (None | PlatformKeyStatus | Unset):
        easypost_api_key (None | str | Unset):
        stripe_secret_key (None | str | Unset):
        stripe_publishable_key (None | str | Unset):
        stripe_webhook_secret (None | str | Unset):
        usage_limit (int | None | Unset):
        description (None | str | Unset):
    """

    status: None | PlatformKeyStatus | Unset = UNSET
    easypost_api_key: None | str | Unset = UNSET
    stripe_secret_key: None | str | Unset = UNSET
    stripe_publishable_key: None | str | Unset = UNSET
    stripe_webhook_secret: None | str | Unset = UNSET
    usage_limit: int | None | Unset = UNSET
    description: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, PlatformKeyStatus):
            status = self.status.value
        else:
            status = self.status

        easypost_api_key: None | str | Unset
        if isinstance(self.easypost_api_key, Unset):
            easypost_api_key = UNSET
        else:
            easypost_api_key = self.easypost_api_key

        stripe_secret_key: None | str | Unset
        if isinstance(self.stripe_secret_key, Unset):
            stripe_secret_key = UNSET
        else:
            stripe_secret_key = self.stripe_secret_key

        stripe_publishable_key: None | str | Unset
        if isinstance(self.stripe_publishable_key, Unset):
            stripe_publishable_key = UNSET
        else:
            stripe_publishable_key = self.stripe_publishable_key

        stripe_webhook_secret: None | str | Unset
        if isinstance(self.stripe_webhook_secret, Unset):
            stripe_webhook_secret = UNSET
        else:
            stripe_webhook_secret = self.stripe_webhook_secret

        usage_limit: int | None | Unset
        if isinstance(self.usage_limit, Unset):
            usage_limit = UNSET
        else:
            usage_limit = self.usage_limit

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if easypost_api_key is not UNSET:
            field_dict["easypost_api_key"] = easypost_api_key
        if stripe_secret_key is not UNSET:
            field_dict["stripe_secret_key"] = stripe_secret_key
        if stripe_publishable_key is not UNSET:
            field_dict["stripe_publishable_key"] = stripe_publishable_key
        if stripe_webhook_secret is not UNSET:
            field_dict["stripe_webhook_secret"] = stripe_webhook_secret
        if usage_limit is not UNSET:
            field_dict["usage_limit"] = usage_limit
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_status(data: object) -> None | PlatformKeyStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = PlatformKeyStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PlatformKeyStatus | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_easypost_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        easypost_api_key = _parse_easypost_api_key(d.pop("easypost_api_key", UNSET))

        def _parse_stripe_secret_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_secret_key = _parse_stripe_secret_key(d.pop("stripe_secret_key", UNSET))

        def _parse_stripe_publishable_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_publishable_key = _parse_stripe_publishable_key(d.pop("stripe_publishable_key", UNSET))

        def _parse_stripe_webhook_secret(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_webhook_secret = _parse_stripe_webhook_secret(d.pop("stripe_webhook_secret", UNSET))

        def _parse_usage_limit(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        usage_limit = _parse_usage_limit(d.pop("usage_limit", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        platform_key_update = cls(
            status=status,
            easypost_api_key=easypost_api_key,
            stripe_secret_key=stripe_secret_key,
            stripe_publishable_key=stripe_publishable_key,
            stripe_webhook_secret=stripe_webhook_secret,
            usage_limit=usage_limit,
            description=description,
        )

        platform_key_update.additional_properties = d
        return platform_key_update

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

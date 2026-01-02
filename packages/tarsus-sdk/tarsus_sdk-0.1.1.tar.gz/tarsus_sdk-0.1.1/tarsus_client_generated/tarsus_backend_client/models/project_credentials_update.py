from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectCredentialsUpdate")


@_attrs_define
class ProjectCredentialsUpdate:
    """Model for updating project credentials securely.

    Attributes:
        easypost_api_key (None | str | Unset):
        stripe_secret_key (None | str | Unset):
        stripe_publishable_key (None | str | Unset):
        stripe_webhook_secret (None | str | Unset):
        smtp_server (None | str | Unset):
        smtp_port (int | None | Unset):
        smtp_username (None | str | Unset):
        smtp_password (None | str | Unset):
        smtp_from_email (None | str | Unset):
        test_credentials (bool | Unset):  Default: False.
    """

    easypost_api_key: None | str | Unset = UNSET
    stripe_secret_key: None | str | Unset = UNSET
    stripe_publishable_key: None | str | Unset = UNSET
    stripe_webhook_secret: None | str | Unset = UNSET
    smtp_server: None | str | Unset = UNSET
    smtp_port: int | None | Unset = UNSET
    smtp_username: None | str | Unset = UNSET
    smtp_password: None | str | Unset = UNSET
    smtp_from_email: None | str | Unset = UNSET
    test_credentials: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        smtp_server: None | str | Unset
        if isinstance(self.smtp_server, Unset):
            smtp_server = UNSET
        else:
            smtp_server = self.smtp_server

        smtp_port: int | None | Unset
        if isinstance(self.smtp_port, Unset):
            smtp_port = UNSET
        else:
            smtp_port = self.smtp_port

        smtp_username: None | str | Unset
        if isinstance(self.smtp_username, Unset):
            smtp_username = UNSET
        else:
            smtp_username = self.smtp_username

        smtp_password: None | str | Unset
        if isinstance(self.smtp_password, Unset):
            smtp_password = UNSET
        else:
            smtp_password = self.smtp_password

        smtp_from_email: None | str | Unset
        if isinstance(self.smtp_from_email, Unset):
            smtp_from_email = UNSET
        else:
            smtp_from_email = self.smtp_from_email

        test_credentials = self.test_credentials

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if easypost_api_key is not UNSET:
            field_dict["easypost_api_key"] = easypost_api_key
        if stripe_secret_key is not UNSET:
            field_dict["stripe_secret_key"] = stripe_secret_key
        if stripe_publishable_key is not UNSET:
            field_dict["stripe_publishable_key"] = stripe_publishable_key
        if stripe_webhook_secret is not UNSET:
            field_dict["stripe_webhook_secret"] = stripe_webhook_secret
        if smtp_server is not UNSET:
            field_dict["smtp_server"] = smtp_server
        if smtp_port is not UNSET:
            field_dict["smtp_port"] = smtp_port
        if smtp_username is not UNSET:
            field_dict["smtp_username"] = smtp_username
        if smtp_password is not UNSET:
            field_dict["smtp_password"] = smtp_password
        if smtp_from_email is not UNSET:
            field_dict["smtp_from_email"] = smtp_from_email
        if test_credentials is not UNSET:
            field_dict["test_credentials"] = test_credentials

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

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

        def _parse_smtp_server(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        smtp_server = _parse_smtp_server(d.pop("smtp_server", UNSET))

        def _parse_smtp_port(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        smtp_port = _parse_smtp_port(d.pop("smtp_port", UNSET))

        def _parse_smtp_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        smtp_username = _parse_smtp_username(d.pop("smtp_username", UNSET))

        def _parse_smtp_password(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        smtp_password = _parse_smtp_password(d.pop("smtp_password", UNSET))

        def _parse_smtp_from_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        smtp_from_email = _parse_smtp_from_email(d.pop("smtp_from_email", UNSET))

        test_credentials = d.pop("test_credentials", UNSET)

        project_credentials_update = cls(
            easypost_api_key=easypost_api_key,
            stripe_secret_key=stripe_secret_key,
            stripe_publishable_key=stripe_publishable_key,
            stripe_webhook_secret=stripe_webhook_secret,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_from_email=smtp_from_email,
            test_credentials=test_credentials,
        )

        project_credentials_update.additional_properties = d
        return project_credentials_update

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

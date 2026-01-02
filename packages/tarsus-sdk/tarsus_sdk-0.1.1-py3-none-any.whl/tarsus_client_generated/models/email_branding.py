from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailBranding")


@_attrs_define
class EmailBranding:
    """Email branding and customization settings for project emails.

    Attributes:
        company_name (None | str | Unset): Company/store name
        company_logo_url (None | str | Unset): URL to company logo image
        primary_color (None | str | Unset): Primary brand color (hex)
        secondary_color (None | str | Unset): Secondary brand color (hex)
        support_email (None | str | Unset): Support contact email
        support_phone (None | str | Unset): Support phone number
        company_address (None | str | Unset): Company physical address
        company_website (None | str | Unset): Company website URL
        footer_text (None | str | Unset): Custom footer text
        show_powered_by (bool | Unset): Show 'Powered by Tarsus' attribution Default: True.
        sender_name (None | str | Unset): Email sender name, e.g., 'The Acme Store Team'
    """

    company_name: None | str | Unset = UNSET
    company_logo_url: None | str | Unset = UNSET
    primary_color: None | str | Unset = UNSET
    secondary_color: None | str | Unset = UNSET
    support_email: None | str | Unset = UNSET
    support_phone: None | str | Unset = UNSET
    company_address: None | str | Unset = UNSET
    company_website: None | str | Unset = UNSET
    footer_text: None | str | Unset = UNSET
    show_powered_by: bool | Unset = True
    sender_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        company_name: None | str | Unset
        if isinstance(self.company_name, Unset):
            company_name = UNSET
        else:
            company_name = self.company_name

        company_logo_url: None | str | Unset
        if isinstance(self.company_logo_url, Unset):
            company_logo_url = UNSET
        else:
            company_logo_url = self.company_logo_url

        primary_color: None | str | Unset
        if isinstance(self.primary_color, Unset):
            primary_color = UNSET
        else:
            primary_color = self.primary_color

        secondary_color: None | str | Unset
        if isinstance(self.secondary_color, Unset):
            secondary_color = UNSET
        else:
            secondary_color = self.secondary_color

        support_email: None | str | Unset
        if isinstance(self.support_email, Unset):
            support_email = UNSET
        else:
            support_email = self.support_email

        support_phone: None | str | Unset
        if isinstance(self.support_phone, Unset):
            support_phone = UNSET
        else:
            support_phone = self.support_phone

        company_address: None | str | Unset
        if isinstance(self.company_address, Unset):
            company_address = UNSET
        else:
            company_address = self.company_address

        company_website: None | str | Unset
        if isinstance(self.company_website, Unset):
            company_website = UNSET
        else:
            company_website = self.company_website

        footer_text: None | str | Unset
        if isinstance(self.footer_text, Unset):
            footer_text = UNSET
        else:
            footer_text = self.footer_text

        show_powered_by = self.show_powered_by

        sender_name: None | str | Unset
        if isinstance(self.sender_name, Unset):
            sender_name = UNSET
        else:
            sender_name = self.sender_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if company_name is not UNSET:
            field_dict["company_name"] = company_name
        if company_logo_url is not UNSET:
            field_dict["company_logo_url"] = company_logo_url
        if primary_color is not UNSET:
            field_dict["primary_color"] = primary_color
        if secondary_color is not UNSET:
            field_dict["secondary_color"] = secondary_color
        if support_email is not UNSET:
            field_dict["support_email"] = support_email
        if support_phone is not UNSET:
            field_dict["support_phone"] = support_phone
        if company_address is not UNSET:
            field_dict["company_address"] = company_address
        if company_website is not UNSET:
            field_dict["company_website"] = company_website
        if footer_text is not UNSET:
            field_dict["footer_text"] = footer_text
        if show_powered_by is not UNSET:
            field_dict["show_powered_by"] = show_powered_by
        if sender_name is not UNSET:
            field_dict["sender_name"] = sender_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_company_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company_name = _parse_company_name(d.pop("company_name", UNSET))

        def _parse_company_logo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company_logo_url = _parse_company_logo_url(d.pop("company_logo_url", UNSET))

        def _parse_primary_color(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        primary_color = _parse_primary_color(d.pop("primary_color", UNSET))

        def _parse_secondary_color(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        secondary_color = _parse_secondary_color(d.pop("secondary_color", UNSET))

        def _parse_support_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        support_email = _parse_support_email(d.pop("support_email", UNSET))

        def _parse_support_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        support_phone = _parse_support_phone(d.pop("support_phone", UNSET))

        def _parse_company_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company_address = _parse_company_address(d.pop("company_address", UNSET))

        def _parse_company_website(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company_website = _parse_company_website(d.pop("company_website", UNSET))

        def _parse_footer_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        footer_text = _parse_footer_text(d.pop("footer_text", UNSET))

        show_powered_by = d.pop("show_powered_by", UNSET)

        def _parse_sender_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sender_name = _parse_sender_name(d.pop("sender_name", UNSET))

        email_branding = cls(
            company_name=company_name,
            company_logo_url=company_logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            support_email=support_email,
            support_phone=support_phone,
            company_address=company_address,
            company_website=company_website,
            footer_text=footer_text,
            show_powered_by=show_powered_by,
            sender_name=sender_name,
        )

        email_branding.additional_properties = d
        return email_branding

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

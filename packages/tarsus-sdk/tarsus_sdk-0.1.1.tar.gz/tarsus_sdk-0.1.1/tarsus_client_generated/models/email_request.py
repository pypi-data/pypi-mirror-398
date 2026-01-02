from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailRequest")


@_attrs_define
class EmailRequest:
    """
    Attributes:
        to (list[str]):
        subject (str):
        body (str):
        html_body (None | str | Unset):
        cc (list[str] | None | Unset):
        bcc (list[str] | None | Unset):
    """

    to: list[str]
    subject: str
    body: str
    html_body: None | str | Unset = UNSET
    cc: list[str] | None | Unset = UNSET
    bcc: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        to = self.to

        subject = self.subject

        body = self.body

        html_body: None | str | Unset
        if isinstance(self.html_body, Unset):
            html_body = UNSET
        else:
            html_body = self.html_body

        cc: list[str] | None | Unset
        if isinstance(self.cc, Unset):
            cc = UNSET
        elif isinstance(self.cc, list):
            cc = self.cc

        else:
            cc = self.cc

        bcc: list[str] | None | Unset
        if isinstance(self.bcc, Unset):
            bcc = UNSET
        elif isinstance(self.bcc, list):
            bcc = self.bcc

        else:
            bcc = self.bcc

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "to": to,
                "subject": subject,
                "body": body,
            }
        )
        if html_body is not UNSET:
            field_dict["html_body"] = html_body
        if cc is not UNSET:
            field_dict["cc"] = cc
        if bcc is not UNSET:
            field_dict["bcc"] = bcc

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        to = cast(list[str], d.pop("to"))

        subject = d.pop("subject")

        body = d.pop("body")

        def _parse_html_body(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        html_body = _parse_html_body(d.pop("html_body", UNSET))

        def _parse_cc(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                cc_type_0 = cast(list[str], data)

                return cc_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        cc = _parse_cc(d.pop("cc", UNSET))

        def _parse_bcc(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bcc_type_0 = cast(list[str], data)

                return bcc_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        bcc = _parse_bcc(d.pop("bcc", UNSET))

        email_request = cls(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            cc=cc,
            bcc=bcc,
        )

        email_request.additional_properties = d
        return email_request

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

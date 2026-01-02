from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddressModel")


@_attrs_define
class AddressModel:
    """Address model for shipping.

    Attributes:
        name (str):
        street1 (str):
        city (str):
        state (str):
        zip_ (str):
        street2 (None | str | Unset):
        country (str | Unset):  Default: 'US'.
        phone (None | str | Unset):
        email (None | str | Unset):
    """

    name: str
    street1: str
    city: str
    state: str
    zip_: str
    street2: None | str | Unset = UNSET
    country: str | Unset = "US"
    phone: None | str | Unset = UNSET
    email: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        street1 = self.street1

        city = self.city

        state = self.state

        zip_ = self.zip_

        street2: None | str | Unset
        if isinstance(self.street2, Unset):
            street2 = UNSET
        else:
            street2 = self.street2

        country = self.country

        phone: None | str | Unset
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "street1": street1,
                "city": city,
                "state": state,
                "zip": zip_,
            }
        )
        if street2 is not UNSET:
            field_dict["street2"] = street2
        if country is not UNSET:
            field_dict["country"] = country
        if phone is not UNSET:
            field_dict["phone"] = phone
        if email is not UNSET:
            field_dict["email"] = email

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        street1 = d.pop("street1")

        city = d.pop("city")

        state = d.pop("state")

        zip_ = d.pop("zip")

        def _parse_street2(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        street2 = _parse_street2(d.pop("street2", UNSET))

        country = d.pop("country", UNSET)

        def _parse_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        address_model = cls(
            name=name,
            street1=street1,
            city=city,
            state=state,
            zip_=zip_,
            street2=street2,
            country=country,
            phone=phone,
            email=email,
        )

        address_model.additional_properties = d
        return address_model

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

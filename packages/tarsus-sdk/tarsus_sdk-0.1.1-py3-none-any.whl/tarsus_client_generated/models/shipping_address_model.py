from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ShippingAddressModel")


@_attrs_define
class ShippingAddressModel:
    """Model for the shipping address associated with an order.
    address_line_2 is optional as single unit addresses don't need it.

        Attributes:
            address_line_1 (str):
            city (str):
            state (str):
            postal_code (str):
            address_line_2 (None | str | Unset):
            country (str | Unset):  Default: 'US'.
    """

    address_line_1: str
    city: str
    state: str
    postal_code: str
    address_line_2: None | str | Unset = UNSET
    country: str | Unset = "US"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address_line_1 = self.address_line_1

        city = self.city

        state = self.state

        postal_code = self.postal_code

        address_line_2: None | str | Unset
        if isinstance(self.address_line_2, Unset):
            address_line_2 = UNSET
        else:
            address_line_2 = self.address_line_2

        country = self.country

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address_line_1": address_line_1,
                "city": city,
                "state": state,
                "postal_code": postal_code,
            }
        )
        if address_line_2 is not UNSET:
            field_dict["address_line_2"] = address_line_2
        if country is not UNSET:
            field_dict["country"] = country

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address_line_1 = d.pop("address_line_1")

        city = d.pop("city")

        state = d.pop("state")

        postal_code = d.pop("postal_code")

        def _parse_address_line_2(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        address_line_2 = _parse_address_line_2(d.pop("address_line_2", UNSET))

        country = d.pop("country", UNSET)

        shipping_address_model = cls(
            address_line_1=address_line_1,
            city=city,
            state=state,
            postal_code=postal_code,
            address_line_2=address_line_2,
            country=country,
        )

        shipping_address_model.additional_properties = d
        return shipping_address_model

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

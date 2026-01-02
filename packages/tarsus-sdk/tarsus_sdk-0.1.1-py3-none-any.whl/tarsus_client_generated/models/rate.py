from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Rate")


@_attrs_define
class Rate:
    """Rate model for shipping rates response.

    Attributes:
        id (str):
        service (str):
        carrier (str):
        rate (float):
        currency (str | Unset):  Default: 'USD'.
        delivery_days (int | None | Unset):
        delivery_date (None | str | Unset):
        shipment_id (None | str | Unset):
    """

    id: str
    service: str
    carrier: str
    rate: float
    currency: str | Unset = "USD"
    delivery_days: int | None | Unset = UNSET
    delivery_date: None | str | Unset = UNSET
    shipment_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        service = self.service

        carrier = self.carrier

        rate = self.rate

        currency = self.currency

        delivery_days: int | None | Unset
        if isinstance(self.delivery_days, Unset):
            delivery_days = UNSET
        else:
            delivery_days = self.delivery_days

        delivery_date: None | str | Unset
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        else:
            delivery_date = self.delivery_date

        shipment_id: None | str | Unset
        if isinstance(self.shipment_id, Unset):
            shipment_id = UNSET
        else:
            shipment_id = self.shipment_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "service": service,
                "carrier": carrier,
                "rate": rate,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency
        if delivery_days is not UNSET:
            field_dict["delivery_days"] = delivery_days
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if shipment_id is not UNSET:
            field_dict["shipment_id"] = shipment_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        service = d.pop("service")

        carrier = d.pop("carrier")

        rate = d.pop("rate")

        currency = d.pop("currency", UNSET)

        def _parse_delivery_days(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        delivery_days = _parse_delivery_days(d.pop("delivery_days", UNSET))

        def _parse_delivery_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

        def _parse_shipment_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        shipment_id = _parse_shipment_id(d.pop("shipment_id", UNSET))

        rate = cls(
            id=id,
            service=service,
            carrier=carrier,
            rate=rate,
            currency=currency,
            delivery_days=delivery_days,
            delivery_date=delivery_date,
            shipment_id=shipment_id,
        )

        rate.additional_properties = d
        return rate

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

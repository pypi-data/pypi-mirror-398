from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.address_model import AddressModel
    from ..models.parcel_model import ParcelModel


T = TypeVar("T", bound="ShipmentRequest")


@_attrs_define
class ShipmentRequest:
    """Request model for creating shipments and getting rates.

    Attributes:
        to_address (AddressModel): Address model for shipping.
        from_address (AddressModel): Address model for shipping.
        parcel (ParcelModel): Parcel model for shipping.
    """

    to_address: AddressModel
    from_address: AddressModel
    parcel: ParcelModel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        to_address = self.to_address.to_dict()

        from_address = self.from_address.to_dict()

        parcel = self.parcel.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "to_address": to_address,
                "from_address": from_address,
                "parcel": parcel,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.address_model import AddressModel
        from ..models.parcel_model import ParcelModel

        d = dict(src_dict)
        to_address = AddressModel.from_dict(d.pop("to_address"))

        from_address = AddressModel.from_dict(d.pop("from_address"))

        parcel = ParcelModel.from_dict(d.pop("parcel"))

        shipment_request = cls(
            to_address=to_address,
            from_address=from_address,
            parcel=parcel,
        )

        shipment_request.additional_properties = d
        return shipment_request

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

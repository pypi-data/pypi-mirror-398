from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.order_status import OrderStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.order_item_model import OrderItemModel
    from ..models.order_model_selected_rate_type_0 import OrderModelSelectedRateType0
    from ..models.shipping_address_model import ShippingAddressModel


T = TypeVar("T", bound="OrderModel")


@_attrs_define
class OrderModel:
    """Complete order with variant/modification support

    Attributes:
        tenant_id (str):
        user_id (str):
        items (list[OrderItemModel]):
        subtotal (float):
        final_total (float):
        id (None | str | Unset):
        project_id (None | str | Unset):
        discount_code (None | str | Unset):
        discount_amount (float | Unset):  Default: 0.0.
        status (OrderStatus | Unset):
        shipping_address (None | ShippingAddressModel | Unset):
        stripe_payment_intent_id (None | str | Unset):
        stripe_payment_status (None | str | Unset):
        stripe_session_id (None | str | Unset):
        selected_rate (None | OrderModelSelectedRateType0 | Unset):
        shipment_id (None | str | Unset):
        tracking_code (None | str | Unset):
        label_url (None | str | Unset):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
    """

    tenant_id: str
    user_id: str
    items: list[OrderItemModel]
    subtotal: float
    final_total: float
    id: None | str | Unset = UNSET
    project_id: None | str | Unset = UNSET
    discount_code: None | str | Unset = UNSET
    discount_amount: float | Unset = 0.0
    status: OrderStatus | Unset = UNSET
    shipping_address: None | ShippingAddressModel | Unset = UNSET
    stripe_payment_intent_id: None | str | Unset = UNSET
    stripe_payment_status: None | str | Unset = UNSET
    stripe_session_id: None | str | Unset = UNSET
    selected_rate: None | OrderModelSelectedRateType0 | Unset = UNSET
    shipment_id: None | str | Unset = UNSET
    tracking_code: None | str | Unset = UNSET
    label_url: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.order_model_selected_rate_type_0 import (
            OrderModelSelectedRateType0,
        )
        from ..models.shipping_address_model import ShippingAddressModel

        tenant_id = self.tenant_id

        user_id = self.user_id

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        subtotal = self.subtotal

        final_total = self.final_total

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        discount_code: None | str | Unset
        if isinstance(self.discount_code, Unset):
            discount_code = UNSET
        else:
            discount_code = self.discount_code

        discount_amount = self.discount_amount

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        shipping_address: dict[str, Any] | None | Unset
        if isinstance(self.shipping_address, Unset):
            shipping_address = UNSET
        elif isinstance(self.shipping_address, ShippingAddressModel):
            shipping_address = self.shipping_address.to_dict()
        else:
            shipping_address = self.shipping_address

        stripe_payment_intent_id: None | str | Unset
        if isinstance(self.stripe_payment_intent_id, Unset):
            stripe_payment_intent_id = UNSET
        else:
            stripe_payment_intent_id = self.stripe_payment_intent_id

        stripe_payment_status: None | str | Unset
        if isinstance(self.stripe_payment_status, Unset):
            stripe_payment_status = UNSET
        else:
            stripe_payment_status = self.stripe_payment_status

        stripe_session_id: None | str | Unset
        if isinstance(self.stripe_session_id, Unset):
            stripe_session_id = UNSET
        else:
            stripe_session_id = self.stripe_session_id

        selected_rate: dict[str, Any] | None | Unset
        if isinstance(self.selected_rate, Unset):
            selected_rate = UNSET
        elif isinstance(self.selected_rate, OrderModelSelectedRateType0):
            selected_rate = self.selected_rate.to_dict()
        else:
            selected_rate = self.selected_rate

        shipment_id: None | str | Unset
        if isinstance(self.shipment_id, Unset):
            shipment_id = UNSET
        else:
            shipment_id = self.shipment_id

        tracking_code: None | str | Unset
        if isinstance(self.tracking_code, Unset):
            tracking_code = UNSET
        else:
            tracking_code = self.tracking_code

        label_url: None | str | Unset
        if isinstance(self.label_url, Unset):
            label_url = UNSET
        else:
            label_url = self.label_url

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "items": items,
                "subtotal": subtotal,
                "final_total": final_total,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if discount_code is not UNSET:
            field_dict["discount_code"] = discount_code
        if discount_amount is not UNSET:
            field_dict["discount_amount"] = discount_amount
        if status is not UNSET:
            field_dict["status"] = status
        if shipping_address is not UNSET:
            field_dict["shipping_address"] = shipping_address
        if stripe_payment_intent_id is not UNSET:
            field_dict["stripe_payment_intent_id"] = stripe_payment_intent_id
        if stripe_payment_status is not UNSET:
            field_dict["stripe_payment_status"] = stripe_payment_status
        if stripe_session_id is not UNSET:
            field_dict["stripe_session_id"] = stripe_session_id
        if selected_rate is not UNSET:
            field_dict["selected_rate"] = selected_rate
        if shipment_id is not UNSET:
            field_dict["shipment_id"] = shipment_id
        if tracking_code is not UNSET:
            field_dict["tracking_code"] = tracking_code
        if label_url is not UNSET:
            field_dict["label_url"] = label_url
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.order_item_model import OrderItemModel
        from ..models.order_model_selected_rate_type_0 import (
            OrderModelSelectedRateType0,
        )
        from ..models.shipping_address_model import ShippingAddressModel

        d = dict(src_dict)
        tenant_id = d.pop("tenant_id")

        user_id = d.pop("user_id")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = OrderItemModel.from_dict(items_item_data)

            items.append(items_item)

        subtotal = d.pop("subtotal")

        final_total = d.pop("final_total")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_discount_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        discount_code = _parse_discount_code(d.pop("discount_code", UNSET))

        discount_amount = d.pop("discount_amount", UNSET)

        _status = d.pop("status", UNSET)
        status: OrderStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = OrderStatus(_status)

        def _parse_shipping_address(
            data: object,
        ) -> None | ShippingAddressModel | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                shipping_address_type_0 = ShippingAddressModel.from_dict(data)

                return shipping_address_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ShippingAddressModel | Unset, data)

        shipping_address = _parse_shipping_address(d.pop("shipping_address", UNSET))

        def _parse_stripe_payment_intent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_payment_intent_id = _parse_stripe_payment_intent_id(d.pop("stripe_payment_intent_id", UNSET))

        def _parse_stripe_payment_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_payment_status = _parse_stripe_payment_status(d.pop("stripe_payment_status", UNSET))

        def _parse_stripe_session_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_session_id = _parse_stripe_session_id(d.pop("stripe_session_id", UNSET))

        def _parse_selected_rate(
            data: object,
        ) -> None | OrderModelSelectedRateType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                selected_rate_type_0 = OrderModelSelectedRateType0.from_dict(data)

                return selected_rate_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrderModelSelectedRateType0 | Unset, data)

        selected_rate = _parse_selected_rate(d.pop("selected_rate", UNSET))

        def _parse_shipment_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        shipment_id = _parse_shipment_id(d.pop("shipment_id", UNSET))

        def _parse_tracking_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_code = _parse_tracking_code(d.pop("tracking_code", UNSET))

        def _parse_label_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        label_url = _parse_label_url(d.pop("label_url", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        order_model = cls(
            tenant_id=tenant_id,
            user_id=user_id,
            items=items,
            subtotal=subtotal,
            final_total=final_total,
            id=id,
            project_id=project_id,
            discount_code=discount_code,
            discount_amount=discount_amount,
            status=status,
            shipping_address=shipping_address,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_payment_status=stripe_payment_status,
            stripe_session_id=stripe_session_id,
            selected_rate=selected_rate,
            shipment_id=shipment_id,
            tracking_code=tracking_code,
            label_url=label_url,
            created_at=created_at,
            updated_at=updated_at,
        )

        order_model.additional_properties = d
        return order_model

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

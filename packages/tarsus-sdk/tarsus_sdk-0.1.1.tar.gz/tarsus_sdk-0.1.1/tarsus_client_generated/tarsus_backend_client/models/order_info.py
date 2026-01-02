from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.order_info_items_item import OrderInfoItemsItem
    from ..models.order_info_tracking_info_type_0 import OrderInfoTrackingInfoType0


T = TypeVar("T", bound="OrderInfo")


@_attrs_define
class OrderInfo:
    """
    Attributes:
        order_id (str):
        items (list[OrderInfoItemsItem]):
        total (float):
        date_purchased (datetime.datetime):
        tracking_info (None | OrderInfoTrackingInfoType0 | Unset):
    """

    order_id: str
    items: list[OrderInfoItemsItem]
    total: float
    date_purchased: datetime.datetime
    tracking_info: None | OrderInfoTrackingInfoType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.order_info_tracking_info_type_0 import OrderInfoTrackingInfoType0

        order_id = self.order_id

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        total = self.total

        date_purchased = self.date_purchased.isoformat()

        tracking_info: dict[str, Any] | None | Unset
        if isinstance(self.tracking_info, Unset):
            tracking_info = UNSET
        elif isinstance(self.tracking_info, OrderInfoTrackingInfoType0):
            tracking_info = self.tracking_info.to_dict()
        else:
            tracking_info = self.tracking_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "order_id": order_id,
                "items": items,
                "total": total,
                "date_purchased": date_purchased,
            }
        )
        if tracking_info is not UNSET:
            field_dict["tracking_info"] = tracking_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.order_info_items_item import OrderInfoItemsItem
        from ..models.order_info_tracking_info_type_0 import OrderInfoTrackingInfoType0

        d = dict(src_dict)
        order_id = d.pop("order_id")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = OrderInfoItemsItem.from_dict(items_item_data)

            items.append(items_item)

        total = d.pop("total")

        date_purchased = isoparse(d.pop("date_purchased"))

        def _parse_tracking_info(data: object) -> None | OrderInfoTrackingInfoType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tracking_info_type_0 = OrderInfoTrackingInfoType0.from_dict(data)

                return tracking_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrderInfoTrackingInfoType0 | Unset, data)

        tracking_info = _parse_tracking_info(d.pop("tracking_info", UNSET))

        order_info = cls(
            order_id=order_id,
            items=items,
            total=total,
            date_purchased=date_purchased,
            tracking_info=tracking_info,
        )

        order_info.additional_properties = d
        return order_info

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

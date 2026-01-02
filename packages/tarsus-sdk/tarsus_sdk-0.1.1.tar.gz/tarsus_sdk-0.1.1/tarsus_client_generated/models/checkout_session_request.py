from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.line_item import LineItem


T = TypeVar("T", bound="CheckoutSessionRequest")


@_attrs_define
class CheckoutSessionRequest:
    """Data model for the request to create a Stripe Checkout Session (payment link).

    Attributes:
        order_id (str):
        line_items (list[LineItem]):
        success_url (str):
        cancel_url (str):
        project_id (None | str | Unset):
    """

    order_id: str
    line_items: list[LineItem]
    success_url: str
    cancel_url: str
    project_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_id = self.order_id

        line_items = []
        for line_items_item_data in self.line_items:
            line_items_item = line_items_item_data.to_dict()
            line_items.append(line_items_item)

        success_url = self.success_url

        cancel_url = self.cancel_url

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "order_id": order_id,
                "line_items": line_items,
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.line_item import LineItem

        d = dict(src_dict)
        order_id = d.pop("order_id")

        line_items = []
        _line_items = d.pop("line_items")
        for line_items_item_data in _line_items:
            line_items_item = LineItem.from_dict(line_items_item_data)

            line_items.append(line_items_item)

        success_url = d.pop("success_url")

        cancel_url = d.pop("cancel_url")

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        checkout_session_request = cls(
            order_id=order_id,
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            project_id=project_id,
        )

        checkout_session_request.additional_properties = d
        return checkout_session_request

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

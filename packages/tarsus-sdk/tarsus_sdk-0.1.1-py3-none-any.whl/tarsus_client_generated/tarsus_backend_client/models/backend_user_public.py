from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.backend_user_public_role import BackendUserPublicRole
from ..models.backend_user_public_subscription_status_type_0 import BackendUserPublicSubscriptionStatusType0
from ..models.backend_user_public_subscription_tier_type_0 import BackendUserPublicSubscriptionTierType0
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackendUserPublic")


@_attrs_define
class BackendUserPublic:
    """Public representation of a backend user (without sensitive data).

    Attributes:
        id (None | str):
        email (str):
        first_name (None | str):
        last_name (None | str):
        role (BackendUserPublicRole):
        is_active (bool):
        created_at (datetime.datetime):
        updated_at (datetime.datetime | None):
        last_login_at (datetime.datetime | None):
        stripe_payment_method_id (None | str | Unset):
        payment_method_last4 (None | str | Unset):
        payment_method_brand (None | str | Unset):
        payment_method_exp_month (int | None | Unset):
        payment_method_exp_year (int | None | Unset):
        stripe_customer_id (None | str | Unset):
        stripe_subscription_id (None | str | Unset):
        subscription_tier (BackendUserPublicSubscriptionTierType0 | None | Unset):
        subscription_status (BackendUserPublicSubscriptionStatusType0 | None | Unset):
        project_count (int | None | Unset):
    """

    id: None | str
    email: str
    first_name: None | str
    last_name: None | str
    role: BackendUserPublicRole
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    last_login_at: datetime.datetime | None
    stripe_payment_method_id: None | str | Unset = UNSET
    payment_method_last4: None | str | Unset = UNSET
    payment_method_brand: None | str | Unset = UNSET
    payment_method_exp_month: int | None | Unset = UNSET
    payment_method_exp_year: int | None | Unset = UNSET
    stripe_customer_id: None | str | Unset = UNSET
    stripe_subscription_id: None | str | Unset = UNSET
    subscription_tier: BackendUserPublicSubscriptionTierType0 | None | Unset = UNSET
    subscription_status: BackendUserPublicSubscriptionStatusType0 | None | Unset = UNSET
    project_count: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        email = self.email

        first_name: None | str
        first_name = self.first_name

        last_name: None | str
        last_name = self.last_name

        role = self.role.value

        is_active = self.is_active

        created_at = self.created_at.isoformat()

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        last_login_at: None | str
        if isinstance(self.last_login_at, datetime.datetime):
            last_login_at = self.last_login_at.isoformat()
        else:
            last_login_at = self.last_login_at

        stripe_payment_method_id: None | str | Unset
        if isinstance(self.stripe_payment_method_id, Unset):
            stripe_payment_method_id = UNSET
        else:
            stripe_payment_method_id = self.stripe_payment_method_id

        payment_method_last4: None | str | Unset
        if isinstance(self.payment_method_last4, Unset):
            payment_method_last4 = UNSET
        else:
            payment_method_last4 = self.payment_method_last4

        payment_method_brand: None | str | Unset
        if isinstance(self.payment_method_brand, Unset):
            payment_method_brand = UNSET
        else:
            payment_method_brand = self.payment_method_brand

        payment_method_exp_month: int | None | Unset
        if isinstance(self.payment_method_exp_month, Unset):
            payment_method_exp_month = UNSET
        else:
            payment_method_exp_month = self.payment_method_exp_month

        payment_method_exp_year: int | None | Unset
        if isinstance(self.payment_method_exp_year, Unset):
            payment_method_exp_year = UNSET
        else:
            payment_method_exp_year = self.payment_method_exp_year

        stripe_customer_id: None | str | Unset
        if isinstance(self.stripe_customer_id, Unset):
            stripe_customer_id = UNSET
        else:
            stripe_customer_id = self.stripe_customer_id

        stripe_subscription_id: None | str | Unset
        if isinstance(self.stripe_subscription_id, Unset):
            stripe_subscription_id = UNSET
        else:
            stripe_subscription_id = self.stripe_subscription_id

        subscription_tier: None | str | Unset
        if isinstance(self.subscription_tier, Unset):
            subscription_tier = UNSET
        elif isinstance(self.subscription_tier, BackendUserPublicSubscriptionTierType0):
            subscription_tier = self.subscription_tier.value
        else:
            subscription_tier = self.subscription_tier

        subscription_status: None | str | Unset
        if isinstance(self.subscription_status, Unset):
            subscription_status = UNSET
        elif isinstance(self.subscription_status, BackendUserPublicSubscriptionStatusType0):
            subscription_status = self.subscription_status.value
        else:
            subscription_status = self.subscription_status

        project_count: int | None | Unset
        if isinstance(self.project_count, Unset):
            project_count = UNSET
        else:
            project_count = self.project_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": is_active,
                "created_at": created_at,
                "updated_at": updated_at,
                "last_login_at": last_login_at,
            }
        )
        if stripe_payment_method_id is not UNSET:
            field_dict["stripe_payment_method_id"] = stripe_payment_method_id
        if payment_method_last4 is not UNSET:
            field_dict["payment_method_last4"] = payment_method_last4
        if payment_method_brand is not UNSET:
            field_dict["payment_method_brand"] = payment_method_brand
        if payment_method_exp_month is not UNSET:
            field_dict["payment_method_exp_month"] = payment_method_exp_month
        if payment_method_exp_year is not UNSET:
            field_dict["payment_method_exp_year"] = payment_method_exp_year
        if stripe_customer_id is not UNSET:
            field_dict["stripe_customer_id"] = stripe_customer_id
        if stripe_subscription_id is not UNSET:
            field_dict["stripe_subscription_id"] = stripe_subscription_id
        if subscription_tier is not UNSET:
            field_dict["subscription_tier"] = subscription_tier
        if subscription_status is not UNSET:
            field_dict["subscription_status"] = subscription_status
        if project_count is not UNSET:
            field_dict["project_count"] = project_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        id = _parse_id(d.pop("id"))

        email = d.pop("email")

        def _parse_first_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        first_name = _parse_first_name(d.pop("first_name"))

        def _parse_last_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_name = _parse_last_name(d.pop("last_name"))

        role = BackendUserPublicRole(d.pop("role"))

        is_active = d.pop("is_active")

        created_at = isoparse(d.pop("created_at"))

        def _parse_updated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        updated_at = _parse_updated_at(d.pop("updated_at"))

        def _parse_last_login_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_login_at_type_0 = isoparse(data)

                return last_login_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_login_at = _parse_last_login_at(d.pop("last_login_at"))

        def _parse_stripe_payment_method_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_payment_method_id = _parse_stripe_payment_method_id(d.pop("stripe_payment_method_id", UNSET))

        def _parse_payment_method_last4(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        payment_method_last4 = _parse_payment_method_last4(d.pop("payment_method_last4", UNSET))

        def _parse_payment_method_brand(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        payment_method_brand = _parse_payment_method_brand(d.pop("payment_method_brand", UNSET))

        def _parse_payment_method_exp_month(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        payment_method_exp_month = _parse_payment_method_exp_month(d.pop("payment_method_exp_month", UNSET))

        def _parse_payment_method_exp_year(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        payment_method_exp_year = _parse_payment_method_exp_year(d.pop("payment_method_exp_year", UNSET))

        def _parse_stripe_customer_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_customer_id = _parse_stripe_customer_id(d.pop("stripe_customer_id", UNSET))

        def _parse_stripe_subscription_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_subscription_id = _parse_stripe_subscription_id(d.pop("stripe_subscription_id", UNSET))

        def _parse_subscription_tier(data: object) -> BackendUserPublicSubscriptionTierType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                subscription_tier_type_0 = BackendUserPublicSubscriptionTierType0(data)

                return subscription_tier_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BackendUserPublicSubscriptionTierType0 | None | Unset, data)

        subscription_tier = _parse_subscription_tier(d.pop("subscription_tier", UNSET))

        def _parse_subscription_status(data: object) -> BackendUserPublicSubscriptionStatusType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                subscription_status_type_0 = BackendUserPublicSubscriptionStatusType0(data)

                return subscription_status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BackendUserPublicSubscriptionStatusType0 | None | Unset, data)

        subscription_status = _parse_subscription_status(d.pop("subscription_status", UNSET))

        def _parse_project_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        project_count = _parse_project_count(d.pop("project_count", UNSET))

        backend_user_public = cls(
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
            stripe_payment_method_id=stripe_payment_method_id,
            payment_method_last4=payment_method_last4,
            payment_method_brand=payment_method_brand,
            payment_method_exp_month=payment_method_exp_month,
            payment_method_exp_year=payment_method_exp_year,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            subscription_tier=subscription_tier,
            subscription_status=subscription_status,
            project_count=project_count,
        )

        backend_user_public.additional_properties = d
        return backend_user_public

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

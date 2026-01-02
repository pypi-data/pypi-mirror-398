from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="APIUsageLog")


@_attrs_define
class APIUsageLog:
    """Model for tracking API key usage.

    Attributes:
        api_key_id (str): ID of the API key used
        backend_user_id (str): ID of the backend user who owns the key
        endpoint (str): API endpoint that was called
        method (str): HTTP method (GET, POST, etc.)
        status_code (int): HTTP status code of the response
        id (None | str | Unset):
        response_time_ms (float | None | Unset): Response time in milliseconds
        request_size_bytes (int | None | Unset): Size of request in bytes
        response_size_bytes (int | None | Unset): Size of response in bytes
        ip_address (None | str | Unset): IP address of the requester
        user_agent (None | str | Unset): User agent of the requester
        error_message (None | str | Unset): Error message if request failed
        created_at (datetime.datetime | Unset):
    """

    api_key_id: str
    backend_user_id: str
    endpoint: str
    method: str
    status_code: int
    id: None | str | Unset = UNSET
    response_time_ms: float | None | Unset = UNSET
    request_size_bytes: int | None | Unset = UNSET
    response_size_bytes: int | None | Unset = UNSET
    ip_address: None | str | Unset = UNSET
    user_agent: None | str | Unset = UNSET
    error_message: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_key_id = self.api_key_id

        backend_user_id = self.backend_user_id

        endpoint = self.endpoint

        method = self.method

        status_code = self.status_code

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        response_time_ms: float | None | Unset
        if isinstance(self.response_time_ms, Unset):
            response_time_ms = UNSET
        else:
            response_time_ms = self.response_time_ms

        request_size_bytes: int | None | Unset
        if isinstance(self.request_size_bytes, Unset):
            request_size_bytes = UNSET
        else:
            request_size_bytes = self.request_size_bytes

        response_size_bytes: int | None | Unset
        if isinstance(self.response_size_bytes, Unset):
            response_size_bytes = UNSET
        else:
            response_size_bytes = self.response_size_bytes

        ip_address: None | str | Unset
        if isinstance(self.ip_address, Unset):
            ip_address = UNSET
        else:
            ip_address = self.ip_address

        user_agent: None | str | Unset
        if isinstance(self.user_agent, Unset):
            user_agent = UNSET
        else:
            user_agent = self.user_agent

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_key_id": api_key_id,
                "backend_user_id": backend_user_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if response_time_ms is not UNSET:
            field_dict["response_time_ms"] = response_time_ms
        if request_size_bytes is not UNSET:
            field_dict["request_size_bytes"] = request_size_bytes
        if response_size_bytes is not UNSET:
            field_dict["response_size_bytes"] = response_size_bytes
        if ip_address is not UNSET:
            field_dict["ip_address"] = ip_address
        if user_agent is not UNSET:
            field_dict["user_agent"] = user_agent
        if error_message is not UNSET:
            field_dict["error_message"] = error_message
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        api_key_id = d.pop("api_key_id")

        backend_user_id = d.pop("backend_user_id")

        endpoint = d.pop("endpoint")

        method = d.pop("method")

        status_code = d.pop("status_code")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_response_time_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time_ms = _parse_response_time_ms(d.pop("response_time_ms", UNSET))

        def _parse_request_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        request_size_bytes = _parse_request_size_bytes(d.pop("request_size_bytes", UNSET))

        def _parse_response_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        response_size_bytes = _parse_response_size_bytes(d.pop("response_size_bytes", UNSET))

        def _parse_ip_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip_address = _parse_ip_address(d.pop("ip_address", UNSET))

        def _parse_user_agent(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_agent = _parse_user_agent(d.pop("user_agent", UNSET))

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        api_usage_log = cls(
            api_key_id=api_key_id,
            backend_user_id=backend_user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            id=id,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            created_at=created_at,
        )

        api_usage_log.additional_properties = d
        return api_usage_log

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

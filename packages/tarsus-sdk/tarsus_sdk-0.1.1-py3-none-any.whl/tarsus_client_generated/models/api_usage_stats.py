from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.api_usage_stats_requests_by_day import APIUsageStatsRequestsByDay
    from ..models.api_usage_stats_requests_by_endpoint import (
        APIUsageStatsRequestsByEndpoint,
    )
    from ..models.api_usage_stats_requests_by_status_code import (
        APIUsageStatsRequestsByStatusCode,
    )


T = TypeVar("T", bound="APIUsageStats")


@_attrs_define
class APIUsageStats:
    """Aggregated API usage statistics.

    Attributes:
        total_requests (int):
        successful_requests (int):
        failed_requests (int):
        average_response_time_ms (float | None):
        requests_by_endpoint (APIUsageStatsRequestsByEndpoint):
        requests_by_status_code (APIUsageStatsRequestsByStatusCode):
        requests_by_day (APIUsageStatsRequestsByDay):
        total_data_transferred_bytes (int | None):
    """

    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float | None
    requests_by_endpoint: APIUsageStatsRequestsByEndpoint
    requests_by_status_code: APIUsageStatsRequestsByStatusCode
    requests_by_day: APIUsageStatsRequestsByDay
    total_data_transferred_bytes: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_requests = self.total_requests

        successful_requests = self.successful_requests

        failed_requests = self.failed_requests

        average_response_time_ms: float | None
        average_response_time_ms = self.average_response_time_ms

        requests_by_endpoint = self.requests_by_endpoint.to_dict()

        requests_by_status_code = self.requests_by_status_code.to_dict()

        requests_by_day = self.requests_by_day.to_dict()

        total_data_transferred_bytes: int | None
        total_data_transferred_bytes = self.total_data_transferred_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "average_response_time_ms": average_response_time_ms,
                "requests_by_endpoint": requests_by_endpoint,
                "requests_by_status_code": requests_by_status_code,
                "requests_by_day": requests_by_day,
                "total_data_transferred_bytes": total_data_transferred_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_usage_stats_requests_by_day import APIUsageStatsRequestsByDay
        from ..models.api_usage_stats_requests_by_endpoint import (
            APIUsageStatsRequestsByEndpoint,
        )
        from ..models.api_usage_stats_requests_by_status_code import (
            APIUsageStatsRequestsByStatusCode,
        )

        d = dict(src_dict)
        total_requests = d.pop("total_requests")

        successful_requests = d.pop("successful_requests")

        failed_requests = d.pop("failed_requests")

        def _parse_average_response_time_ms(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        average_response_time_ms = _parse_average_response_time_ms(d.pop("average_response_time_ms"))

        requests_by_endpoint = APIUsageStatsRequestsByEndpoint.from_dict(d.pop("requests_by_endpoint"))

        requests_by_status_code = APIUsageStatsRequestsByStatusCode.from_dict(d.pop("requests_by_status_code"))

        requests_by_day = APIUsageStatsRequestsByDay.from_dict(d.pop("requests_by_day"))

        def _parse_total_data_transferred_bytes(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        total_data_transferred_bytes = _parse_total_data_transferred_bytes(d.pop("total_data_transferred_bytes"))

        api_usage_stats = cls(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time_ms=average_response_time_ms,
            requests_by_endpoint=requests_by_endpoint,
            requests_by_status_code=requests_by_status_code,
            requests_by_day=requests_by_day,
            total_data_transferred_bytes=total_data_transferred_bytes,
        )

        api_usage_stats.additional_properties = d
        return api_usage_stats

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

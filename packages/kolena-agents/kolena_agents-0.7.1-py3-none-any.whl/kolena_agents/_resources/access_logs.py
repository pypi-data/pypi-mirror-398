from typing import Optional

import kolena_agents.types.access_logs as access_logs_types
from kolena_agents._generated.openapi_client import ApiClient  # type: ignore
from kolena_agents._generated.openapi_client.api import ClientApi  # type: ignore


class AccessLogs:
    def __init__(self, client: ApiClient) -> None:
        """Initialize the AccessLogs resource.

        Args:
            client: The configured API client instance.
        """
        self._api = ClientApi(client)

    def query(
        self,
        time_range: Optional[access_logs_types.ClientTimeRange] = None,
        filters: Optional[access_logs_types.LogFilters] = None,
        page_size: Optional[int] = 100,
        cursor: Optional[str] = None,
    ) -> access_logs_types.ClientQueryAccessLogsResponse:
        """Query access logs with optional filtering and pagination.

        Args:
            time_range: Optional time range filter for the logs
            filters: Optional filters to apply to the log query
            page_size: Number of items per page (default: 100, max: 10000)
            cursor: Pagination cursor for retrieving subsequent pages

        Returns:
            Response containing access log events and pagination metadata
        """
        request = access_logs_types.ClientQueryAccessLogsRequest(
            time_range=time_range,
            filters=filters,
            page_size=page_size,
            cursor=cursor,
        )

        return self._api.client_query_access_logs_api_v1_client_access_logs_query_put(
            client_query_access_logs_request=request
        )

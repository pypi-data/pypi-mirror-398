"""Data client for querying metrics from Glaium Data Service."""

from __future__ import annotations

import os
from typing import Any

import httpx

from glaium.exceptions import APIError, ConnectionError, TimeoutError

# Environment variable for API URL (goes through authorization gateway)
API_URL_ENV = "GLAIUM_API_URL"
DEFAULT_API_URL = "https://edge.glaium.io/api"


class DataClient:
    """
    Client for querying metrics from the Glaium Data Service.

    Example:
        ```python
        from glaium.extras import DataClient

        data_client = DataClient()

        # Query metrics
        result = await data_client.retrieve(
            organization_id=123,
            metrics=["spend", "installs", "cpi"],
            dimensions=["campaign_id", "country"],
            period=["d-7", "d-1"],
        )

        # Convenience methods
        campaigns = await data_client.get_campaign_performance(org_id=123, days=7)
        trends = await data_client.get_daily_trends(org_id=123, metric="installs", days=14)
        ```
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the data client.

        Args:
            base_url: API gateway URL. Falls back to GLAIUM_API_URL env var.
            api_key: API key for authentication (required for authorization).
            timeout: Request timeout in seconds.
        """
        self._base_url = (
            base_url or os.environ.get(API_URL_ENV) or DEFAULT_API_URL
        ).rstrip("/")
        self._api_key = api_key or os.environ.get("GLAIUM_API_KEY")
        self._timeout = timeout

        self._async_client: httpx.AsyncClient | None = None
        self._sync_client: httpx.Client | None = None

    @property
    def _async(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._async_client

    @property
    def _sync(self) -> httpx.Client:
        """Get or create sync HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._sync_client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            # Use 'apiKey' header for API gateway authentication
            headers["apiKey"] = self._api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response."""
        if response.status_code == 200:
            return response.json()

        try:
            error_body = response.json()
            error_message = error_body.get("detail", str(error_body))
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"

        raise APIError(error_message, status_code=response.status_code)

    # =========================================================================
    # Core Methods
    # =========================================================================

    async def retrieve(
        self,
        organization_id: int,
        metrics: list[str],
        dimensions: list[str] | None = None,
        period: list[str] | None = None,
        conditional: str | None = None,
        output: str = "json",
        anonymize: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieve metrics from Data Service.

        Args:
            organization_id: Organization context.
            metrics: List of metrics (e.g., ["spend", "installs", "cpi"]).
            dimensions: Grouping dimensions (e.g., ["campaign_id", "country"]).
            period: Date range (e.g., ["d-7", "d-1"] for last 7 days).
            conditional: Filter conditions.
            output: Output format (default "json").
            anonymize: Apply anonymization to KPIs marked with anonymize=True.
                Default is False (opt-in). Set to True when sending data to LLMs.

        Returns:
            Dict with requested data.
        """
        payload = {
            "organization_id": organization_id,
            "metrics": metrics,
            "dimensions": dimensions or [],
            "period": period or ["d-7", "d-1"],
            "conditional": conditional,
            "output": output,
            "anonymize": anonymize,
        }

        try:
            response = await self._async.post(
                "/data/retrieve",
                json=payload,
                headers=self._get_headers(),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to data service: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        return self._handle_response(response)

    def retrieve_sync(
        self,
        organization_id: int,
        metrics: list[str],
        dimensions: list[str] | None = None,
        period: list[str] | None = None,
        conditional: str | None = None,
        output: str = "json",
        anonymize: bool = False,
    ) -> dict[str, Any]:
        """Sync version of retrieve()."""
        payload = {
            "organization_id": organization_id,
            "metrics": metrics,
            "dimensions": dimensions or [],
            "period": period or ["d-7", "d-1"],
            "conditional": conditional,
            "output": output,
            "anonymize": anonymize,
        }

        try:
            response = self._sync.post(
                "/data/retrieve",
                json=payload,
                headers=self._get_headers(),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to data service: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        return self._handle_response(response)

    # =========================================================================
    # De-anonymization
    # =========================================================================

    async def deanonymize(
        self,
        data: str | list[dict[str, Any]] | dict[str, Any],
        data_type: str = "auto",
    ) -> str | list[dict[str, Any]] | dict[str, Any]:
        """
        De-anonymize data containing anonymized patterns (e.g., app§§963D9D63B7701FC5).

        Anonymized values follow the pattern {kpi}§§{hash} and are automatically
        created when querying KPIs marked with anonymize=True. Use this method
        to reveal the original values when presenting results to authorized users.

        The organization is determined automatically from your API key, ensuring
        you can only de-anonymize your own organization's data.

        Args:
            data: Data to de-anonymize. Can be:
                - A string containing anonymized patterns
                - A list of dicts (dataframe-like structure)
                - A single dict
            data_type: Type of data. Options:
                - "auto": Automatically detect based on input type (default)
                - "string": Treat as plain text
                - "markdown": Treat as markdown text
                - "dataframe": Treat as list of dicts

        Returns:
            De-anonymized data in the same format as input.

        Example:
            ```python
            # De-anonymize a string
            text = "Revenue for app§§963D9D63B7701FC5 is $1000"
            clear_text = await client.deanonymize(data=text)
            # Returns: "Revenue for Contraction Tracker is $1000"

            # De-anonymize query results
            result = await client.retrieve(organization_id=123, metrics=["revenue"], dimensions=["app"])
            clear_result = await client.deanonymize(data=result["data"])
            ```

        Note:
            Requires a valid API key. The organization is determined from the API key,
            so you can only de-anonymize data belonging to your organization.
        """
        # Auto-detect data type
        if data_type == "auto":
            if isinstance(data, str):
                data_type = "string"
            elif isinstance(data, list):
                data_type = "dataframe"
            elif isinstance(data, dict):
                # Single dict - wrap in list for API
                data_type = "dataframe"
                data = [data]
            else:
                raise ValueError(f"Cannot auto-detect data type for {type(data)}")

        payload = {
            "data_type": data_type,
            "data": data,
        }

        try:
            response = await self._async.post(
                "/data/deanonymize",
                json=payload,
                headers=self._get_headers(),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        result = self._handle_response(response)
        return result.get("data", data)

    def deanonymize_sync(
        self,
        data: str | list[dict[str, Any]] | dict[str, Any],
        data_type: str = "auto",
    ) -> str | list[dict[str, Any]] | dict[str, Any]:
        """
        Sync version of deanonymize().

        See deanonymize() for full documentation.
        """
        # Auto-detect data type
        if data_type == "auto":
            if isinstance(data, str):
                data_type = "string"
            elif isinstance(data, list):
                data_type = "dataframe"
            elif isinstance(data, dict):
                data_type = "dataframe"
                data = [data]
            else:
                raise ValueError(f"Cannot auto-detect data type for {type(data)}")

        payload = {
            "data_type": data_type,
            "data": data,
        }

        try:
            response = self._sync.post(
                "/data/deanonymize",
                json=payload,
                headers=self._get_headers(),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        result = self._handle_response(response)
        return result.get("data", data)

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_campaign_performance(
        self,
        organization_id: int,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get campaign performance metrics.

        Args:
            organization_id: Organization ID.
            days: Number of days to look back.

        Returns:
            Campaign performance data.
        """
        return await self.retrieve(
            organization_id=organization_id,
            metrics=["spend", "installs", "revenue", "cpi", "roas"],
            dimensions=["campaign_id", "campaign_name", "network"],
            period=[f"d-{days}", "d-1"],
        )

    async def get_daily_trends(
        self,
        organization_id: int,
        metric: str,
        days: int = 14,
    ) -> list[dict[str, Any]]:
        """
        Get daily trend for a specific metric.

        Args:
            organization_id: Organization ID.
            metric: Metric name (e.g., "installs", "spend").
            days: Number of days to look back.

        Returns:
            List of daily values.
        """
        result = await self.retrieve(
            organization_id=organization_id,
            metrics=[metric],
            dimensions=["day"],
            period=[f"d-{days}", "d-1"],
        )
        return result.get("data", [])

    async def get_aggregated_metrics(
        self,
        organization_id: int,
        metrics: list[str],
        days: int = 7,
    ) -> dict[str, float]:
        """
        Get aggregated metrics without dimensions.

        Args:
            organization_id: Organization ID.
            metrics: List of metrics.
            days: Number of days to aggregate.

        Returns:
            Dict mapping metric name to value.
        """
        result = await self.retrieve(
            organization_id=organization_id,
            metrics=metrics,
            dimensions=[],
            period=[f"d-{days}", "d-1"],
        )
        data = result.get("data", [{}])
        if data:
            return {m: data[0].get(m, 0) for m in metrics}
        return {m: 0 for m in metrics}

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def aclose(self) -> None:
        """Close async client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def close(self) -> None:
        """Close sync client."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def __aenter__(self) -> "DataClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    def __enter__(self) -> "DataClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

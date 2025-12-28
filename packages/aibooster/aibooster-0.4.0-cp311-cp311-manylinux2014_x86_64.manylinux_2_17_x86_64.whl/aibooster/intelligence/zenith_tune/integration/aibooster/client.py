from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger("zenith-tune")


class AIBoosterClient:
    """AIBooster API client for interacting with AIBooster server endpoints.

    This client provides both low-level (raw JSON) and high-level (structured data)
    access to the AIBooster server API. The public methods return structured data
    for ease of use, while methods with _ prefix return the original JSON responses.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        skip_health_check: bool = False,
    ):
        """Initialize the AIBooster client.

        Args:
            base_url: Base URL for the AIBooster API
            timeout: Request timeout in seconds
            skip_health_check: Skip initial connection verification

        Raises:
            ConnectionError: If health check fails (unless skip_health_check=True)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = self._create_session()

        # Verify connection unless explicitly skipped
        if not skip_health_check and not self.health_check():
            raise ConnectionError(
                f"Failed to connect to AIBooster server at {base_url}. "
                "Server may be down or URL may be incorrect."
            )

    def _create_session(self) -> requests.Session:
        """Create a requests session with basic retry configuration.

        Returns:
            Configured requests session with retry adapter
        """
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=3)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request and return JSON response.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (will be appended to base_url)
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed for {method} {path}: {e}")
            raise

    # ========== Health Check ==========

    def _health_check(self) -> Dict[str, Any]:
        """Get raw health check response.

        Returns:
            Raw health check JSON response

        Raises:
            requests.RequestException: If the request fails
        """
        return self._request_json("GET", "/")

    def health_check(self) -> bool:
        """Check if the AIBooster server is healthy.

        Returns:
            True if the server is healthy, False otherwise
        """
        try:
            data = self._health_check()
            return data.get("message") == "healthly"
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Health check failed: {e}")
            return False

    # ========== DCGM Metrics ==========

    def _get_dcgm_metrics(
        self,
        metric_name: str,
        begin_time: datetime | None = None,
        end_time: datetime | None = None,
        agents: Optional[List[str]] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Dict[str, Any]:
        """Get raw DCGM metrics response.

        Args:
            metric_name: Name of the DCGM metric
            begin_time: Begin time for the query
            end_time: End time for the query
            agents: List of agent hostnames to filter
            limit: Maximum number of records (1-10000)
            offset: Offset for pagination

        Returns:
            Raw DCGM metrics JSON response

        Raises:
            requests.RequestException: If the request fails
        """
        params = {"metric_name": metric_name}
        if begin_time:
            params["begin_time"] = (
                begin_time.isoformat()
                if isinstance(begin_time, datetime)
                else begin_time
            )
        if end_time:
            params["end_time"] = (
                end_time.isoformat() if isinstance(end_time, datetime) else end_time
            )
        if agents:
            params["agents"] = agents
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return self._request_json("GET", "/api/v1/metrics/dcgm", params)

    def get_dcgm_metrics(
        self,
        metric_name: str,
        begin_time: datetime | None = None,
        end_time: datetime | None = None,
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
    ) -> dict[str, dict[int, list[Dict[str, Any]]]]:
        r"""Get all DCGM metrics for the specified period.

        This method automatically handles pagination to retrieve all available
        metrics data within the specified time range.

        Args:
            metric_name: Name of the DCGM metric to retrieve.
                Allowed values:
                - DCGM_FI_DEV_GPU_UTIL
                - DCGM_FI_DEV_MEM_COPY_UTIL
                - DCGM_FI_DEV_SM_CLOCK
                - DCGM_FI_DEV_MEM_CLOCK
                - DCGM_FI_DEV_FB_USED
                - DCGM_FI_DEV_FB_FREE
                - DCGM_FI_DEV_POWER_USAGE
                - DCGM_FI_DEV_TEMPERATURE_CURRENT
                - DCGM_FI_DEV_SM_OCCUPANCY
                - DCGM_FI_DEV_MEMORY_TEMP
                - DCGM_FI_DEV_PCIE_TX_THROUGHPUT
                - DCGM_FI_DEV_PCIE_RX_THROUGHPUT
                - DCGM_FI_DEV_MEMORY_UTIL
            begin_time: Begin time for the query (defaults to UNIX epoch)
            end_time: End time for the query (defaults to current time)
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)

        Returns:
            Dictionary: hostname -> gpu_index -> list of \{timestamp, value\} dicts

        Raises:
            requests.RequestException: If the request fails
        """
        all_metrics = defaultdict(lambda: defaultdict(list))
        offset = 0
        limit = 10000

        # Extract agents list from agent_gpu_filter if provided
        agent_filter = list(agent_gpu_filter.keys()) if agent_gpu_filter else None

        while True:
            data = self._get_dcgm_metrics(
                metric_name, begin_time, end_time, agent_filter, limit, offset
            )

            # Parse and aggregate data from this page
            for agent_data in data.get("agents", []):
                hostname = agent_data["hostname"]

                # Skip agents not in filter if filter is specified (defensive check)
                if agent_gpu_filter and hostname not in agent_gpu_filter:
                    continue

                for gpu_data in agent_data.get("gpus", []):
                    gpu_index = gpu_data["gpu_index"]

                    # Skip GPUs not in filter if filter is specified
                    if agent_gpu_filter and gpu_index not in agent_gpu_filter[hostname]:
                        continue

                    timeseries = [
                        {
                            "timestamp": datetime.fromisoformat(
                                point["timestamp"].replace("Z", "+00:00")
                            ),
                            "value": point["value"],
                        }
                        for point in gpu_data.get("timeseries", [])
                    ]
                    all_metrics[hostname][gpu_index].extend(timeseries)

            # Check if there are more pages
            next_offset = data.get("next_offset")
            if next_offset is None:
                break
            offset = next_offset

        return dict(all_metrics)

    def get_dcgm_metrics_reduction(
        self,
        metric_name: str,
        reduction: str = "mean",
        begin_time: datetime | None = None,
        end_time: datetime | None = None,
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
    ) -> float | None:
        """Get statistical reduction of DCGM metrics.

        This method retrieves all DCGM metrics and computes statistical summaries
        for each GPU across the specified time range.

        Args:
            metric_name: Name of the DCGM metric to retrieve.
                Allowed values:
                - DCGM_FI_DEV_GPU_UTIL
                - DCGM_FI_DEV_MEM_COPY_UTIL
                - DCGM_FI_DEV_SM_CLOCK
                - DCGM_FI_DEV_MEM_CLOCK
                - DCGM_FI_DEV_FB_USED
                - DCGM_FI_DEV_FB_FREE
                - DCGM_FI_DEV_POWER_USAGE
                - DCGM_FI_DEV_TEMPERATURE_CURRENT
                - DCGM_FI_DEV_SM_OCCUPANCY
                - DCGM_FI_DEV_MEMORY_TEMP
                - DCGM_FI_DEV_PCIE_TX_THROUGHPUT
                - DCGM_FI_DEV_PCIE_RX_THROUGHPUT
                - DCGM_FI_DEV_MEMORY_UTIL
            reduction: Statistical reduction to apply ("mean", "max", "min", "median")
            begin_time: Begin time for the query (defaults to UNIX epoch)
            end_time: End time for the query (defaults to current time)
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)

        Returns:
            Single statistical value as float, or None if no data is available

        Raises:
            ValueError: If reduction type is invalid
            requests.RequestException: If the request fails
        """
        # Get all raw metrics first
        metrics = self.get_dcgm_metrics(
            metric_name, begin_time, end_time, agent_gpu_filter
        )

        # Collect all values from all GPUs and all time points
        all_values = []
        for gpu_metrics in metrics.values():
            for timeseries in gpu_metrics.values():
                all_values.extend([point["value"] for point in timeseries])

        # Handle empty data case
        if not all_values:
            return None

        # Compute specified statistical reduction
        if reduction == "mean":
            return statistics.mean(all_values)
        elif reduction == "max":
            return max(all_values)
        elif reduction == "min":
            return min(all_values)
        elif reduction == "median":
            return statistics.median(all_values)
        else:
            raise ValueError(
                f"Unsupported reduction: {reduction}. Use 'mean', 'max', 'min', or 'median'."
            )

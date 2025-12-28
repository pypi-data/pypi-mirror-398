import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..integration.aibooster import AIBoosterClient
from .base import AutoPrunerBase

logger = logging.getLogger("zenith-tune")


class AIBoosterDCGMMetricsPruner(AutoPrunerBase):
    """Prune based on AIBooster DCGM metrics conditions."""

    def __init__(
        self,
        aibooster_server_address: str,
        metric_name: str,
        threshold: float,
        prune_when: str = "below",
        reduction: str = "mean",
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
        check_interval: float = 10.0,
        warmup_duration: float = 60.0,
    ):
        """Initialize AIBooster DCGM metrics pruner.

        Pruning logic:
        1. Waits for warmup_duration seconds after trial start (skips monitoring)
        2. After warmup, checks metrics every check_interval seconds
        3. For each check, calculates the statistical value (mean/min/max/median)
           from metrics collected in the last check_interval period
        4. Prunes if the statistical value meets the threshold condition

        Example: With default settings (warmup=60s, interval=10s, reduction="mean"),
        starts monitoring after 60 seconds, then every 10 seconds calculates the
        mean value of metrics from the last 10 seconds and compares with threshold.

        Args:
            aibooster_server_address: AIBooster server address
            metric_name: DCGM metric to monitor
            threshold: Metric threshold for pruning
            prune_when: When to prune - "below" or "above" the threshold
            reduction: Statistical reduction method ("mean", "max", "min", "median")
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)
            check_interval: Interval between metric checks in seconds
            warmup_duration: Warmup period before starting checks in seconds (60+ seconds recommended)
        """
        if prune_when not in ("below", "above"):
            raise ValueError("prune_when must be 'below' or 'above'")
        if reduction not in ("mean", "max", "min", "median"):
            raise ValueError("reduction must be 'mean', 'max', 'min', or 'median'")

        self.aibooster_server_address = aibooster_server_address
        self.metric_name = metric_name
        self.threshold = threshold
        self.prune_when = prune_when
        self.reduction = reduction
        self.agent_gpu_filter = agent_gpu_filter
        self.check_interval = check_interval
        self.warmup_duration = warmup_duration

        self.client = AIBoosterClient(aibooster_server_address, skip_health_check=True)
        self.on_start()

    def on_start(self) -> None:
        """Called when command execution starts."""
        self.start_time = time.time()
        self.last_check_time = 0.0

    def on_end(self) -> None:
        """Called when command execution ends."""
        execution_time = time.time() - self.start_time
        if execution_time < self.warmup_duration:
            logger.warning(
                f"Execution ended in {execution_time:.1f} seconds, less than warmup period ({self.warmup_duration}s). "
                "Pruning was not active during this execution."
            )

    def should_prune(self) -> bool:
        """Check if command should be terminated based on metrics."""
        current_time = time.time()

        # Don't check during warmup period
        if current_time - self.start_time < self.warmup_duration:
            return False

        # Don't check too frequently
        if current_time - self.last_check_time < self.check_interval:
            return False

        self.last_check_time = current_time

        try:
            # Get metrics for last check_interval period
            end_time = datetime.now(timezone.utc)
            begin_time = end_time - timedelta(seconds=self.check_interval)

            value = self.client.get_dcgm_metrics_reduction(
                self.metric_name,
                self.reduction,
                begin_time=begin_time,
                end_time=end_time,
                agent_gpu_filter=self.agent_gpu_filter,
            )

            if value is None:
                return False

            # Apply comparison based on prune_when setting
            prune_triggered = False
            if self.prune_when == "above":
                prune_triggered = value > self.threshold
            else:  # "below"
                prune_triggered = value < self.threshold

            # Only log when pruning is triggered
            if prune_triggered:
                logger.info(
                    f"Pruning triggered: {self.metric_name} ({self.reduction}): {value:.2f}, threshold: {self.threshold}, prune_when: {self.prune_when}"
                )

            return prune_triggered

        except Exception as e:
            logger.error(f"Error checking AIBooster metrics: {e}")
            return False


class AIBoosterGPUUtilizationPruner(AIBoosterDCGMMetricsPruner):
    """Prune based on GPU utilization below threshold."""

    def __init__(
        self,
        aibooster_server_address: str,
        threshold: float,
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
        check_interval: float = 10.0,
        warmup_duration: float = 60.0,
    ):
        """Initialize GPU utilization pruner.

        Args:
            aibooster_server_address: AIBooster server address (e.g., "http://localhost:16697")
            threshold: GPU utilization threshold below which to prune (e.g., 5.0 for 5%)
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)
            check_interval: Interval between metric checks in seconds
            warmup_duration: Warmup period before starting checks in seconds (60+ seconds recommended)
        """
        super().__init__(
            aibooster_server_address,
            "DCGM_FI_DEV_GPU_UTIL",
            threshold,
            "below",
            "mean",
            agent_gpu_filter,
            check_interval,
            warmup_duration,
        )


class AIBoosterGPUMemoryUsedPruner(AIBoosterDCGMMetricsPruner):
    """Prune based on GPU memory usage (MB) above threshold."""

    def __init__(
        self,
        aibooster_server_address: str,
        threshold: float,
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
        check_interval: float = 10.0,
        warmup_duration: float = 60.0,
    ):
        """Initialize GPU memory utilization pruner.

        Args:
            aibooster_server_address: AIBooster server address (e.g., "http://localhost:16697")
            threshold: GPU memory usage threshold in MB above which to prune
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)
            check_interval: Interval between metric checks in seconds
            warmup_duration: Warmup period before starting checks in seconds (60+ seconds recommended)
        """
        super().__init__(
            aibooster_server_address,
            "DCGM_FI_DEV_FB_USED",
            threshold,
            "above",
            "mean",
            agent_gpu_filter,
            check_interval,
            warmup_duration,
        )


class AIBoosterTemperaturePruner(AIBoosterDCGMMetricsPruner):
    """Prune based on GPU temperature above threshold."""

    def __init__(
        self,
        aibooster_server_address: str,
        threshold: float,
        agent_gpu_filter: Optional[Dict[str, List[int]]] = None,
        check_interval: float = 10.0,
        warmup_duration: float = 60.0,
    ):
        """Initialize GPU temperature pruner.

        Args:
            aibooster_server_address: AIBooster server address (e.g., "http://localhost:16697")
            threshold: GPU temperature threshold above which to prune
            agent_gpu_filter: Dict of agent_name -> [gpu_indices] to filter specific GPUs (None = all)
            check_interval: Interval between metric checks in seconds
            warmup_duration: Warmup period before starting checks in seconds (60+ seconds recommended)
        """
        super().__init__(
            aibooster_server_address,
            "DCGM_FI_DEV_GPU_TEMP",
            threshold,
            "above",
            "mean",
            agent_gpu_filter,
            check_interval,
            warmup_duration,
        )

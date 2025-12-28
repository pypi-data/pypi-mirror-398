import time

from .base import AutoPrunerBase


class TimeoutPruner(AutoPrunerBase):
    """Prune based on execution time limit."""

    def __init__(self, timeout: float):
        self.timeout = timeout
        self.on_start()

    def on_start(self) -> None:
        """Called when command execution starts."""
        self.start_time = time.time()

    def on_end(self) -> None:
        """Called when command execution ends."""
        # Clean up resources if needed
        pass

    def should_prune(self) -> bool:
        elapsed_time = time.time() - self.start_time
        return elapsed_time > self.timeout

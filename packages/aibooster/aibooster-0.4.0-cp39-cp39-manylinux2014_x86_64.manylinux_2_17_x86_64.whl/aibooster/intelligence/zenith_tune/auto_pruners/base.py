from abc import ABC, abstractmethod


class AutoPrunerBase(ABC):
    """
    Abstract base class for automatic execution pruners.

    Pruners monitor execution and can terminate processes based on custom conditions.
    Multiple pruners can be active simultaneously.
    """

    @abstractmethod
    def should_prune(self) -> bool:
        """
        Check if the command should be terminated.

        Returns:
            bool: True if command should be terminated, False otherwise
        """

    @abstractmethod
    def on_start(self) -> None:
        """
        Called when command execution starts.

        This method is called before command execution begins to initialize
        the pruner's internal state and prepare for monitoring.
        """

    @abstractmethod
    def on_end(self) -> None:
        """
        Called when command execution ends.

        This method is called after command execution completes (whether successful,
        failed, or pruned) to clean up resources and perform final operations.
        """

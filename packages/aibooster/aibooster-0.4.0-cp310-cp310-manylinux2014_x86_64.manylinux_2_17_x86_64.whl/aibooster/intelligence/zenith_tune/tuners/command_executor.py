import logging
import os
import signal
import subprocess
import threading
import time
from typing import Dict, List, Optional, Union

from ..auto_pruners import AutoPrunerBase
from ..distributed import get_dist_info

logger = logging.getLogger("zenith-tune")


class CommandExecutor:
    """
    Command execution functionality with auto pruner support.
    """

    def __init__(
        self,
        auto_pruners: Optional[List[AutoPrunerBase]] = None,
        poll_interval: float = 0.1,
        dist_info: Optional[Dict[str, Union[int, str]]] = None,
    ):
        """
        Initialize the CommandExecutor.

        Args:
            auto_pruners: List of auto pruners to monitor during execution
            poll_interval: Polling interval in seconds. Defaults to 0.1
            dist_info: Distribution information for rank checking. If None, will be obtained automatically.
        """
        self.auto_pruners = auto_pruners
        self.poll_interval = poll_interval
        self.dist_info = dist_info or get_dist_info()

    def run(
        self,
        command: str,
        log_path: Optional[str] = None,
    ) -> bool:
        """
        Run a command with optional logging and polling.

        Args:
            command (str): The command to execute.
            log_path (Optional[str]): The log file path. If provided, enables logging.

        Returns:
            bool: True if command completed successfully, False if timed out, pruned, or failed.
        """
        if log_path:
            # Only rank 0 writes the initial command and environment
            if self.dist_info["rank"] == 0:
                subprocess.run(
                    f"echo '{command}' > {log_path}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    f"env >> {log_path}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            command += f" >> {log_path} 2>&1"

        # Call on_start for all pruners
        if self.auto_pruners:
            for pruner in self.auto_pruners:
                pruner.on_start()

        # Start process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,  # Create new process group
        )

        # Initialize pruner monitoring
        pruned = threading.Event()
        pruner_thread = None
        pruned_name = None

        if self.auto_pruners:

            def monitor_pruners():
                nonlocal pruned_name

                while not pruned.is_set() and process.poll() is None:
                    for pruner in self.auto_pruners:
                        try:
                            if pruner.should_prune():
                                pruned_name = pruner.__class__.__name__
                                pruned.set()
                                return
                        except Exception:
                            # Log pruner errors but continue monitoring
                            pass

                    time.sleep(self.poll_interval)

            pruner_thread = threading.Thread(target=monitor_pruners, daemon=True)
            pruner_thread.start()

        # Polling loop
        try:
            while process.poll() is None:
                # Check for pruning
                if pruned.is_set():
                    logger.info(f"Process pruned by {pruned_name}")
                    CommandExecutor._terminate_process_group(process)
                    return False

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            CommandExecutor._terminate_process_group(process)
            raise
        finally:
            # Ensure subprocess is terminated if still running
            if process.poll() is None:
                CommandExecutor._terminate_process_group(process)

            # Signal monitoring thread to stop and wait for it to finish
            if pruner_thread and pruner_thread.is_alive():
                pruned.set()
                # Wait up to 1 second for thread to finish
                pruner_thread.join(timeout=1.0)

            # Call on_end for all pruners
            if self.auto_pruners:
                for pruner in self.auto_pruners:
                    pruner.on_end()

        # Check return code
        return process.returncode == 0

    @staticmethod
    def _terminate_process_group(process):
        """
        Terminate process group with graceful fallback to force kill.

        Args:
            process: subprocess.Popen instance
        """
        try:
            # Send SIGTERM to entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)

            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if still alive
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()  # Clean up zombie process

        except (ProcessLookupError, OSError):
            # Process group already terminated or doesn't exist
            pass

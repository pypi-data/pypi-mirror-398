import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from optuna.pruners import BasePruner
from optuna.samplers import BaseSampler
from optuna.trial import Trial

from ..auto_pruners import AutoPrunerBase
from .command_executor import CommandExecutor
from .function_runtime import FunctionRuntimeTuner


class CommandRuntimeTuner(FunctionRuntimeTuner):
    """
    A tuner for executing runtime commands.
    """

    def __init__(
        self,
        output_dir: str = "outputs",
        study_name: Optional[str] = None,
        db_path: Optional[str] = None,
        sampler: Optional[BaseSampler] = None,
        pruner: Optional[BasePruner] = None,
        auto_pruners: Optional[List[AutoPrunerBase]] = None,
        maximize: bool = False,
    ) -> None:
        """
        Initialize the CommandRuntimeTuner.

        Args:
            output_dir (str): The directory to store the study results. Defaults to "outputs".
            study_name (str): The name of the study. Defaults to None.
            db_path (Optional[str]): The path to the database file. Defaults to None.
            sampler (Optional[BaseSampler]): The sampler to use. Defaults to None.
            pruner (Optional[BasePruner]): The pruner to use. Defaults to None.
            auto_pruners (Optional[List[AutoPrunerBase]]): List of auto pruners to monitor during execution. Defaults to None.
            maximize (bool): Whether to maximize the objective function. Defaults to False.
        """
        super().__init__(
            output_dir=output_dir,
            study_name=study_name,
            db_path=db_path,
            sampler=sampler,
            pruner=pruner,
            maximize=maximize,
        )
        self.executor = CommandExecutor(auto_pruners, dist_info=self.dist_info)

    def optimize(
        self,
        command_generator: Callable[..., str],
        n_trials: int,
        default_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Optimize the given objective function using Optuna.

        Args:
            command_generator (Callable[..., str]): A function that generates the command to execute.
            n_trials (int): The number of trials to run.
            default_params (Optional[Dict[str, Any]]): Default parameters to use for the optimization.

        Returns:
            Tuple[float, Dict[str, Any]]: The best value and parameters found during optimization.
        """

        def new_objective(
            trial: Trial,
            trial_id: int,
            dist_info: Dict[str, Union[int, str]],
            study_dir: str,
            **kwargs,
        ):
            command = command_generator(trial, **kwargs)
            if command is None:
                return None

            filename = f"trial_{trial_id}.txt"
            log_path = os.path.join(study_dir, filename)

            success = self.executor.run(command=command, log_path=log_path)
            # If the command was pruned, return None to indicate pruning to Optuna
            if not success:
                return None

        return super().optimize(new_objective, n_trials, default_params)

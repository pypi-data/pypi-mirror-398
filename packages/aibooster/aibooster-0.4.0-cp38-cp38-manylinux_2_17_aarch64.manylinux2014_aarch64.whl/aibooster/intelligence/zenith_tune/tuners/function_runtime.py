import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from optuna.pruners import BasePruner
from optuna.samplers import BaseSampler
from optuna.trial import Trial

from ..auto_pruners import AutoPrunerBase
from .general import GeneralTuner

logger = logging.getLogger("zenith-tune")


class FunctionRuntimeTuner(GeneralTuner):
    """
    A tuner for runtime optimization.
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
        Initialize the FunctionRuntimeTuner.

        Args:
            output_dir (str): The directory to store the study results. Defaults to "outputs".
            study_name (str): The name of the study. Defaults to None.
            db_path (Optional[str]): The path to the database file. Defaults to None.
            sampler (Optional[BaseSampler]): The sampler to use. Defaults to None.
            pruner (Optional[BasePruner]): The pruner to use. Defaults to None.
            auto_pruners (Optional[List[AutoPrunerBase]]): List of auto pruners to monitor during execution. Defaults to None.
            maximize (bool): Whether to maximize the objective function. Defaults to False.
        """
        # FunctionRuntimeTuner doesn't support auto_pruners
        if auto_pruners:
            logger.warning(
                "auto_pruners are not supported in FunctionRuntimeTuner and will be ignored."
            )
        super().__init__(
            output_dir=output_dir,
            study_name=study_name,
            db_path=db_path,
            sampler=sampler,
            pruner=pruner,
            maximize=maximize,
        )

    def optimize(
        self,
        func: Callable[..., Any],
        n_trials: int,
        default_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Optimize the given objective function using Optuna.

        Args:
            func (Callable[..., Any]): The objective function to optimize.
            n_trials (int): The number of trials to run.
            default_params (Optional[Dict[str, Any]]): Default parameters to use for the optimization.

        Returns:
            Tuple[float, Dict[str, Any]]: The best value and parameters found during optimization.
        """

        def new_objective(trial: Trial, **kwargs):
            t_begin = time.perf_counter()
            func(trial, **kwargs)
            t_end = time.perf_counter()
            return t_end - t_begin

        return super().optimize(new_objective, n_trials, default_params)

import datetime
import logging
import os
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

import optuna
from optuna.pruners import BasePruner
from optuna.samplers import BaseSampler
from optuna.trial import Trial

from ..auto_pruners import AutoPrunerBase
from ..distributed import get_dist_info, get_launcher

logger = logging.getLogger("zenith-tune")


if get_launcher() is not None:
    try:
        import torch.distributed as dist
    except ImportError:
        raise ImportError(
            "torch is not installed. PyTorch is required for distributed environments in zenith-tune. "
            "Visit https://pytorch.org/get-started/locally/ for installation instructions."
        )


class GeneralTuner:
    """
    Base class for tuners.
    """

    BARRIER_TIMEOUT = 3600  # seconds

    def __init__(
        self,
        output_dir: str = "outputs",
        study_name: str = None,
        db_path: Optional[str] = None,
        sampler: Optional[BaseSampler] = None,
        pruner: Optional[BasePruner] = None,
        auto_pruners: Optional[List[AutoPrunerBase]] = None,
        maximize: bool = False,
        callbacks: Optional[List[Callable]] = None,
    ) -> None:
        """
        Initialize the GeneralTuner.

        Args:
            output_dir (str): The directory to store the study results. Defaults to "outputs".
            study_name (str): The name of the study. Defaults to None.
            db_path (Optional[str]): The path to the database file. Defaults to None.
            sampler (Optional[BaseSampler]): The sampler to use. Defaults to None.
            pruner (Optional[BasePruner]): The pruner to use. Defaults to None.
            auto_pruners (Optional[List[AutoPrunerBase]]): List of auto pruners to monitor during execution. Defaults to None.
            maximize (bool): Whether to maximize the objective function. Defaults to False.
            callbacks (Optional[List[Callable]]): List of Optuna callbacks. Defaults to None.
        """
        self.dist_info = get_dist_info()
        if self.dist_info["launcher"] == "torch":
            assert "MASTER_ADDR" in os.environ
            assert "MASTER_PORT" in os.environ

            # Pre-initializing for optuna.integration.TorchDistributedTrial
            if not dist.is_initialized():
                dist.init_process_group("gloo")

            # Avoiding port conflicts for torchrun
            master_addr = os.environ["MASTER_ADDR"]
            master_port = int(os.environ["MASTER_PORT"])
            new_master_port = master_port + 1
            new_endpoint = f"{master_addr}:{master_port + 2}"
            os.environ["MASTER_PORT"] = str(new_master_port)
            os.environ["PET_RDZV_ENDPOINT"] = new_endpoint
            os.environ["TORCHELASTIC_USE_AGENT_STORE"] = "False"
        elif self.dist_info["launcher"] == "mpi":
            # Pre-initializing for optuna.integration.TorchDistributedTrial
            if not dist.is_initialized():
                dist.init_process_group("mpi")

        if self.dist_info["rank"] == 0:
            logger.info(f"Using distributed launcher: {self.dist_info['launcher']}")

        self.maximize = maximize
        self.callbacks = callbacks or []

        # GeneralTuner doesn't support auto_pruners directly
        if auto_pruners:
            logger.warning(
                "auto_pruners are not supported in GeneralTuner and will be ignored."
            )

        if db_path is not None:
            if output_dir is not None and study_name is not None:
                logger.warning(
                    "Both db_path and (output_dir, study_name) are specified. "
                    "db_path will be prioritized and (output_dir, study_name) will be ignored."
                )
            if not os.path.exists(db_path):
                raise FileNotFoundError(db_path)
            self.study_dir = os.path.dirname(db_path)
            self.study_name = os.path.split(self.study_dir)[1]
        else:
            if study_name is None:
                study_name = "study_" + datetime.datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
            self.study_name = study_name
            self.study_dir = os.path.join(output_dir, self.study_name)
            db_path = os.path.join(self.study_dir, "study.db")

        assert db_path

        # Optuna setup
        if os.path.exists(db_path):
            # load
            self.is_load_study = True

            self.study = optuna.load_study(
                storage=f"sqlite:///{db_path}", study_name=self.study_name
            )
            self.trial_id = len(self.study.trials)
            self.study_uuid = self.study.user_attrs.get("study_uuid")
        else:
            # create
            self.is_load_study = False

            if self.dist_info["rank"] == 0:
                os.makedirs(self.study_dir, exist_ok=True)
                self.study = optuna.create_study(
                    storage="sqlite:///" + db_path,
                    sampler=sampler,
                    pruner=pruner,
                    study_name=study_name,
                    direction="maximize" if self.maximize else None,
                    load_if_exists=True,
                )
                # Generate and save study UUID
                self.study_uuid = str(uuid.uuid4())
                self.study.set_user_attr("study_uuid", self.study_uuid)
            self.trial_id = 0

        # Initialize OpenTelemetry callback if OTEL_COLLECTOR_ENDPOINT is set
        if self.dist_info["rank"] == 0:
            self._init_otel_callback()

        if self.dist_info["launcher"] is not None:
            work = dist.barrier(async_op=True)
            if not work.wait(timeout=datetime.timedelta(seconds=self.BARRIER_TIMEOUT)):
                raise TimeoutError(
                    f"Barrier timed out after {self.BARRIER_TIMEOUT} seconds."
                )

    def _init_otel_callback(self):
        """Initialize OpenTelemetry callback if OTEL_COLLECTOR_ENDPOINT environment variable is set."""
        otel_endpoint = os.environ.get("OTEL_COLLECTOR_ENDPOINT")
        if otel_endpoint is None:
            return

        logger.info(f"OTEL_COLLECTOR_ENDPOINT detected: {otel_endpoint}")
        try:
            from ..integration.opentelemetry import OpenTelemetryCallback

            # Check if OpenTelemetry callback already exists to prevent duplicates
            if not any(isinstance(cb, OpenTelemetryCallback) for cb in self.callbacks):
                attributes = self._get_otel_attributes()
                otel_callback = OpenTelemetryCallback(
                    endpoint=otel_endpoint,
                    attributes=attributes,
                )
                self.callbacks.append(otel_callback)
                logger.info(
                    f"OpenTelemetry callback added to callbacks with endpoint: {otel_endpoint}"
                )
            else:
                logger.info("OpenTelemetry callback already exists, skipping duplicate")
        except ImportError:
            logger.warning(
                "OpenTelemetry dependencies not available. Metrics will not be exported."
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry callback: {e}")

    def _get_otel_attributes(self):
        """Get additional attributes for OpenTelemetry callback."""
        return {
            "study.name": self.study_name,
            "study.uuid": self.study_uuid,
            "tuner": self.__class__.__name__,
            "maximize": str(self.maximize),
        }

    # ToDo: timeout feature, pass user args
    def optimize(
        self,
        objective: Callable[..., Optional[float]],
        n_trials: int,
        default_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Optimize the given objective function using Optuna.

        Args:
            objective (Callable[..., Optional[float]]): The objective function to optimize.
            n_trials (int): The number of trials to run.
            default_params (Optional[Dict[str, Any]]): Default parameters to use for the first optimization.

        Returns:
            Tuple[float, Dict[str, Any]]: The best value and parameters found during optimization.
        """

        def objective_wrapper(trial: Trial):
            if self.dist_info["world_size"] > 1:
                trial = optuna.integration.TorchDistributedTrial(trial)

            try:
                ret = objective(
                    trial,
                    trial_id=self.trial_id,
                    dist_info=self.dist_info,
                    study_dir=self.study_dir,
                )
            except Exception as e:
                self.trial_id += 1
                logger.error(f"Trial failed: {e}", exc_info=True)
                raise optuna.TrialPruned()

            self.trial_id += 1
            if self.dist_info["rank"] == 0 and ret is None:
                raise optuna.TrialPruned()
            return ret

        if self.dist_info["rank"] == 0:
            if default_params is not None and not self.is_load_study:
                self.study.enqueue_trial(default_params)

            self.study.optimize(
                lambda trial: objective_wrapper(trial),
                n_trials=n_trials,
                callbacks=self.callbacks if self.callbacks else None,
            )

            try:
                best_trial = self.study.best_trial
                best_value, best_params = best_trial.value, best_trial.params
            except Exception as e:
                logger.error(e)
                best_value, best_params = None, {}
        else:
            for _ in range(n_trials):
                objective_wrapper(None)
            best_value, best_params = None, {}

        if self.dist_info["launcher"] is not None:
            work = dist.barrier(async_op=True)
            if not work.wait(timeout=datetime.timedelta(seconds=self.BARRIER_TIMEOUT)):
                raise TimeoutError(
                    f"Barrier timed out after {self.BARRIER_TIMEOUT} seconds."
                )

        return best_value, best_params

    def analyze(
        self,
        plot_contour: bool = True,
        plot_importances: bool = True,
        plot_history: bool = True,
        plot_timeline: bool = True,
    ) -> None:
        """
        Analyze the optimization results.

        Args:
            plot_contour (bool): Whether to plot the contour plot. Defaults to True.
            plot_importances (bool): Whether to plot the parameter importances. Defaults to True.
            plot_history (bool): Whether to plot the optimization history. Defaults to True.
            plot_timeline (bool): Whether to plot the timeline. Defaults to True.
        """
        if self.dist_info["rank"] != 0:
            return
        if len(self.study.trials) == 0:
            logger.error("Trials are not included in study.")
            return

        first_trial = self.study.trials[0]
        logger.info(
            f"First trial: value={first_trial.value}, params={first_trial.params}"
        )

        try:
            best_trial = self.study.best_trial
            logger.info(
                f"Best trial: trial_id={best_trial._trial_id}, value={best_trial.value}, params={best_trial.params}"
            )
            if first_trial.value is not None:
                improvement_rate = (
                    best_trial.value / first_trial.value
                    if self.maximize
                    else first_trial.value / best_trial.value
                )
                logger.info(f"Improvement rate from first: {improvement_rate}")
        except Exception as e:
            logger.error(e, exc_info=True)
            return

        if plot_contour:
            fig = optuna.visualization.plot_contour(self.study)
            fig.write_html(os.path.join(self.study_dir, "contour.html"))
        if plot_importances:
            fig = optuna.visualization.plot_param_importances(self.study)
            fig.write_image(os.path.join(self.study_dir, "importances.png"))
        if plot_history:
            fig = optuna.visualization.plot_optimization_history(self.study)
            fig.update_layout(yaxis=dict(title="Objective Value"))
            fig.write_image(os.path.join(self.study_dir, "history.png"))
        if plot_timeline:
            fig = optuna.visualization.plot_timeline(self.study)
            fig.write_image(os.path.join(self.study_dir, "timeline.png"))

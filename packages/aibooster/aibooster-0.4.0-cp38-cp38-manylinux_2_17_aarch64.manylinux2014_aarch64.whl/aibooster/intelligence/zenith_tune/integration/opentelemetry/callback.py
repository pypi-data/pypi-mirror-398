"""OpenTelemetry logs callback for Optuna optimization tracking."""

import json
import logging
import time
from typing import Any, Dict, Optional

import optuna
from opentelemetry import _logs, trace
from opentelemetry._logs import SeverityNumber
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from optuna.trial import FrozenTrial, TrialState

logger = logging.getLogger("zenith-tune")


class OpenTelemetryCallback:
    """
    Callback to export Optuna trial logs to OpenTelemetry.

    This callback logs each trial as a single structured log record containing:
    - Trial number, state, and value
    - Trial parameters (as JSON)
    - Best value so far
    """

    def __init__(
        self,
        endpoint: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the OpenTelemetry callback.

        Args:
            endpoint: OTLP endpoint (required)
            attributes: Additional attributes to add to resource and logs
        """
        self.attributes = attributes or {}

        # Setup OpenTelemetry logs
        self._setup_otel(endpoint)

    def _setup_otel(self, endpoint: str):
        """Setup OpenTelemetry logs provider."""
        # Create resource with service information and user attributes
        resource_attributes = {
            "service.name": "ZenithTune",
        }
        if self.attributes:
            resource_attributes.update(self.attributes)

        resource = Resource.create(resource_attributes)

        # Setup OTLP log exporter
        otlp_exporter = OTLPLogExporter(
            endpoint=endpoint,
            insecure=True,  # For development; use secure in production
        )

        # Create log record processor
        log_processor = BatchLogRecordProcessor(otlp_exporter)

        # Create and set logger provider
        provider = LoggerProvider(resource=resource)
        provider.add_log_record_processor(log_processor)
        _logs.set_logger_provider(provider)

        # Get logger for this callback and store resource for log records
        self._otel_logger = _logs.get_logger(__name__)
        self._resource = resource

    def __call__(self, study: optuna.Study, trial: FrozenTrial):
        """
        Callback function called after each trial.

        Args:
            study: The Optuna study
            trial: The completed trial
        """
        # Get best value from study
        try:
            best_value = study.best_value
        except ValueError:
            # No completed trials yet
            best_value = None

        # Prepare log attributes (serialize params as JSON)
        log_attributes = {
            "trial.number": trial.number,
            "trial.state": trial.state.name,
            "trial.params": json.dumps(trial.params),
            "trial.value": trial.value if trial.value is not None else "null",
            "best_value": best_value if best_value is not None else "null",
            "timestamp": time.time_ns(),
        }

        # Determine log level and message based on trial state
        if trial.state == TrialState.COMPLETE:
            severity_number = SeverityNumber.INFO
            severity_text = "INFO"
            message = f"Trial {trial.number} completed with value {trial.value}"
        elif trial.state == TrialState.PRUNED:
            severity_number = SeverityNumber.WARN
            severity_text = "WARNING"
            message = f"Trial {trial.number} was pruned"
        elif trial.state == TrialState.FAIL:
            severity_number = SeverityNumber.ERROR
            severity_text = "ERROR"
            message = f"Trial {trial.number} failed"
        else:
            severity_number = SeverityNumber.INFO
            severity_text = "INFO"
            message = f"Trial {trial.number} finished with state {trial.state.name}"

        # Create and emit log record
        log_record = LogRecord(
            timestamp=time.time_ns(),
            trace_id=0,
            span_id=0,
            trace_flags=trace.TraceFlags.DEFAULT,
            severity_number=severity_number,
            severity_text=severity_text,
            body=message,
            resource=self._resource,
            attributes=log_attributes,
        )
        self._otel_logger.emit(log_record)

"""
Clarvynn - Intelligent OpenTelemetry Sampling with CPL Governance

A pip-installable package that integrates with OpenTelemetry's auto-instrumentation
via the Configurator pattern, using Deferred Head Sampling for intelligent decisions
based on actual request outcomes.

Usage:
    # Install
    pip install clarvynn
    pip install opentelemetry-distro opentelemetry-exporter-otlp

    # Bootstrap OpenTelemetry
    opentelemetry-bootstrap -a install

    # Enable Clarvynn
    export CLARVYNN_ENABLED=true
    export CLARVYNN_POLICY_PATH=/etc/clarvynn/policy.yaml

    # Run with instrumentation
    opentelemetry-instrument python app.py
"""

__version__ = "0.3.1"
__author__ = "Clarvynn Team"
__description__ = (
    "Intelligent Deferred Head Sampling for OpenTelemetry with policy-driven governance"
)

__all__ = [
    "ClarvynnConfigurator",
    "ClarvynnSpanProcessor",
    "get_logger",
    "configure_logging",
    "set_log_level",
]

from clarvynn.configurator import ClarvynnConfigurator
from clarvynn.logging import configure_logging, get_logger, set_log_level
from clarvynn.processors.clarvynn_span_processor import ClarvynnSpanProcessor

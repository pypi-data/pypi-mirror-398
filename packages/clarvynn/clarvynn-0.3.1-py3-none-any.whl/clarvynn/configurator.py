"""
OpenTelemetry Configurator Plugin for Clarvynn.

This class is auto-discovered by opentelemetry-instrument via entry_points.
It hooks into OpenTelemetry's initialization to add Clarvynn's SpanProcessor.

ARCHITECTURE NOTE: Uses SpanProcessor (tail-based) NOT Sampler (head-based)
This allows evaluation of actual request outcomes (status_code, duration, errors).
"""

import os
from typing import Optional

from clarvynn.logging import configure_logging, get_logger, log_startup_block
from opentelemetry import trace
from opentelemetry.sdk._configuration import _OTelSDKConfigurator, logging
from opentelemetry.sdk.trace import TracerProvider

logger = get_logger("configurator")
_basic_config_patched = False
_original_basic_config = None


def _patch_basic_config_for_logging_bridge():
    """
    Allow user logging.basicConfig to work even when Clarvynn attaches a handler first.

    OTel logging auto-instrumentation installs a handler on the root logger. When we
    attach our bridge handler before the user's code runs, logging.basicConfig normally
    becomes a no-op (root already has handlers) which silently blocks app log levels and
    console handlers. We temporarily remove only Clarvynn bridge handlers so the user's
    basicConfig call can proceed, then restore them.
    """

    global _basic_config_patched, _original_basic_config

    if _basic_config_patched:
        return

    import logging as python_logging

    # If we've already wrapped basicConfig elsewhere, unwrap to the true original
    base_basic_config = getattr(
        python_logging.basicConfig, "__clarvynn_wrapped_basic_config__", python_logging.basicConfig
    )
    _original_basic_config = base_basic_config

    def clarvynn_friendly_basic_config(*args, **kwargs):
        force = kwargs.get("force", False)
        root_logger = python_logging.getLogger()

        try:
            from opentelemetry.sdk._logs import LoggingHandler as OTelLoggingHandler

            if not isinstance(OTelLoggingHandler, type):
                # In tests this may be patched to a MagicMock/callable
                OTelLoggingHandler = None
        except Exception:
            OTelLoggingHandler = None

        clarvynn_handlers = [
            h for h in root_logger.handlers if getattr(h, "_clarvynn_logging_bridge", False)
        ]

        def _is_otel_handler(h):
            if not OTelLoggingHandler:
                return False
            try:
                return isinstance(h, OTelLoggingHandler)
            except TypeError:
                return False

        otel_handlers = [h for h in root_logger.handlers if _is_otel_handler(h)]

        # If only Clarvynn/OTel bridge handlers are present (no user handlers) and force is not set,
        # temporarily remove them so basicConfig can attach console/file handlers.
        intercept_handlers = clarvynn_handlers + otel_handlers
        user_handlers = [h for h in root_logger.handlers if h not in intercept_handlers]

        if intercept_handlers and not user_handlers and not force:
            for handler in intercept_handlers:
                root_logger.removeHandler(handler)
            try:
                return _original_basic_config(*args, **kwargs)
            finally:
                # Re-add a single Clarvynn bridge (if any) and a single OTel LoggingHandler (if any)
                if clarvynn_handlers:
                    root_logger.addHandler(clarvynn_handlers[0])
                if otel_handlers:
                    root_logger.addHandler(otel_handlers[0])
        elif intercept_handlers and not user_handlers and force:
            # logging.basicConfig(force=True) will clear all handlers; mimic that behavior
            for handler in list(root_logger.handlers):
                root_logger.removeHandler(handler)
            result = _original_basic_config(*args, **kwargs)
            if clarvynn_handlers:
                root_logger.addHandler(clarvynn_handlers[0])
            if otel_handlers:
                root_logger.addHandler(otel_handlers[0])
            return result

        return _original_basic_config(*args, **kwargs)

    clarvynn_friendly_basic_config.__clarvynn_wrapped_basic_config__ = base_basic_config
    python_logging.basicConfig = clarvynn_friendly_basic_config
    _basic_config_patched = True


class ClarvynnConfigurator(_OTelSDKConfigurator):
    """
    Integrates Clarvynn with OpenTelemetry auto-instrumentation.

    Activated when CLARVYNN_ENABLED=true environment variable is set.

    This follows OpenTelemetry's standard configurator pattern and is
    automatically discovered via the entry_points mechanism in setup.py.

    ARCHITECTURE: Uses SpanProcessor for Deferred Head Sampling, which evaluates
    spans AFTER they complete, allowing intelligent decisions based on actual
    request outcomes (errors, slow requests, critical paths).
    """

    def _configure(self, **kwargs):
        """
        Called by opentelemetry-instrument during initialization.

        This runs AFTER OpenTelemetry creates the TracerProvider but
        BEFORE auto-instrumentation is applied to the user's app.

        WHAT THIS DOES:
        1. Calls parent to initialize OpenTelemetry SDK
        2. Loads CPL policy from file
        3. Creates ProductionCPLAdapter (orchestrator)
        4. Creates ClarvynnSpanProcessor (tail-based evaluator)
        5. Adds processor to TracerProvider
        6. Sets up logging correlation

        Returns:
            None if configuration succeeds or Clarvynn is disabled
        """

        # Configure Clarvynn logging based on environment
        log_level = os.getenv("CLARVYNN_LOG_LEVEL", "warning")
        configure_logging(level=log_level)

        logger.debug("ClarvynnConfigurator._configure() called")
        logger.debug(f"CLARVYNN_ENABLED={os.getenv('CLARVYNN_ENABLED')}")

        enabled = os.getenv("CLARVYNN_ENABLED", "false").lower() == "true"

        if not enabled:
            logger.debug("Clarvynn not enabled (CLARVYNN_ENABLED != true)")
            # Fall back to default OTel initialization
            super()._configure(**kwargs)
            return

        # Call parent to initialize TracerProvider, but we'll manage processors
        logger.debug("Calling parent to initialize TracerProvider")
        super()._configure(**kwargs)
        logger.debug("TracerProvider initialized")

        logger.info("Clarvynn governance initializing...")

        try:
            policy_path = os.getenv("CLARVYNN_POLICY_PATH", "/etc/clarvynn/policy.yaml")

            if not os.path.exists(policy_path):
                logger.error(f"❌ Policy file not found: {policy_path}")
                logger.error("   Set CLARVYNN_POLICY_PATH to valid policy file")
                return

            from core.cpl_engine.python.production_cpl_adapter import ProductionCPLAdapter

            logger.info(f"Loading policy from: {policy_path}")
            adapter = ProductionCPLAdapter(policy_file=policy_path)
            adapter.setup()

            tracer_provider = trace.get_tracer_provider()

            # 2. Initialize Clarvynn components
            if not isinstance(tracer_provider, TracerProvider):
                logger.warning("TracerProvider is not SDK TracerProvider")
                logger.warning("Clarvynn may not work correctly")
                logger.warning("Ensure opentelemetry-instrument is running")
                return

            # Respect OTEL_TRACES_EXPORTER for display; we will reuse the auto-configured pipeline.
            traces_exporter = os.getenv("OTEL_TRACES_EXPORTER", "otlp")
            logger.debug(f"OTEL_TRACES_EXPORTER={traces_exporter}")

            # Thin Needle: steal the auto-configured BatchSpanProcessor instead of recreating exporters.
            original_processor = None
            if hasattr(tracer_provider, "_active_span_processor"):
                active_processor = tracer_provider._active_span_processor
                if hasattr(active_processor, "_span_processors"):
                    from opentelemetry.sdk.trace.export import BatchSpanProcessor

                    processors = list(active_processor._span_processors)
                    for p in processors:
                        if isinstance(p, BatchSpanProcessor):
                            original_processor = p
                            break

                    if original_processor:
                        processors.remove(original_processor)
                        active_processor._span_processors = tuple(processors)
                        logger.debug("✓ Intercepted OTel BatchSpanProcessor for downstream export")
                    else:
                        logger.warning("Could not find BatchSpanProcessor in active processors")
                else:
                    logger.warning("Active processor has no _span_processors; cannot intercept")
            else:
                logger.warning("TracerProvider has no _active_span_processor; cannot intercept")

            if not original_processor:
                # Fallback to a minimal processor so Clarvynn can still operate.
                logger.warning("⚠️ Using fallback SimpleSpanProcessor(ConsoleSpanExporter)")
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

                original_processor = SimpleSpanProcessor(ConsoleSpanExporter())

            from clarvynn.processors.batch_exporter_adapter import ProcessorToExporterAdapter
            from clarvynn.processors.clarvynn_span_processor import ClarvynnSpanProcessor
            from clarvynn.processors.tracestate_exporter import ClarvynnTraceStateExporter

            # Wrap the intercepted processor so it looks like an exporter to Clarvynn.
            downstream_exporter = ProcessorToExporterAdapter(original_processor)

            # Wrap with TraceState exporter for W3C TraceContext Level 2 support.
            tracestate_exporter = ClarvynnTraceStateExporter(downstream_exporter, adapter)

            # Initialize Log Buffer for Flight Recorder
            from core.cpl_engine.python.log_buffer import SharedRingBuffer

            # Flight Recorder Configuration
            max_logs = int(os.getenv("CLARVYNN_MAX_LOGS_PER_TRACE", "100"))
            max_traces = int(os.getenv("CLARVYNN_MAX_ACTIVE_TRACES", "10000"))
            ttl_seconds = int(os.getenv("CLARVYNN_FLIGHT_RECORDER_TTL", "300"))

            logger.debug(
                f"Flight Recorder Config: max_logs={max_logs}, max_traces={max_traces}, ttl={ttl_seconds}s"
            )

            log_buffer = SharedRingBuffer(
                max_logs_per_trace=max_logs, max_active_traces=max_traces, ttl_seconds=ttl_seconds
            )

            # Create processor with wrapped exporter and log buffer
            # Note: We pass log_exporter=None initially, it will be set by _setup_log_filtering
            processor = ClarvynnSpanProcessor(adapter, tracestate_exporter, log_buffer=log_buffer)

            tracer_provider.add_span_processor(processor)

            # Set up log filtering (and update processor with log exporter)
            self._setup_log_filtering(adapter, processor, log_buffer)

            # Log startup information
            conditions_list = "\n".join(
                [f"   - {cond.name}: {cond.when}" for cond in adapter.get_conditions()]
            )

            # Determine endpoint info for display
            if traces_exporter == "console":
                endpoint_display = "console (stdout/stderr)"
            elif traces_exporter == "otlp" or traces_exporter.startswith("otlp"):
                endpoint_display = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            else:
                endpoint_display = traces_exporter

            log_startup_block(
                "configurator",
                "Clarvynn Governance Enabled Successfully",
                {
                    "Service": os.getenv("OTEL_SERVICE_NAME", "unknown"),
                    "Base sampling rate": f"{adapter.get_base_rate() * 100:.1f}%",
                    "CPL conditions": len(adapter.get_conditions()),
                    "Evaluation": "Tail-based (after request completes)",
                    "W3C TraceContext Level 2": "Enabled",
                    "Log filtering": "Enabled (correlated to trace sampling)",
                    "Flight Recorder": "Enabled (Conditional Log Buffering)",
                    "Traces Exporter": endpoint_display,
                },
            )

            if len(adapter.get_conditions()) > 0:
                logger.info("CPL Conditions:")
                for cond in adapter.get_conditions():
                    logger.info(f"   - {cond.name}: {cond.when}")

        except ImportError as e:
            logger.error(f"❌ Failed to import Clarvynn components: {e}")
            logger.error("   Is clarvynn package installed correctly?")

        except Exception as e:
            logger.error(f"❌ Clarvynn initialization failed: {e}")
            logger.error("   Application will continue without Clarvynn governance")
            import traceback

            traceback.print_exc()

    def _setup_log_filtering(self, adapter, span_processor, log_buffer):
        """
        Set up log filtering correlated to trace sampling.

        Logs associated with exported traces are kept.
        Logs associated with dropped traces are dropped.
        This ensures logs and traces are consistently sampled.

        Args:
            adapter: ProductionCPLAdapter for policy evaluation
            span_processor: ClarvynnSpanProcessor with trace decision cache
            log_buffer: SharedRingBuffer for Flight Recorder
        """
        try:
            import logging as python_logging

            from clarvynn.processors.clarvynn_log_processor import ClarvynnLogProcessor
            from opentelemetry import _logs as logs_api
            from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler

            logger.debug("Setting up log filtering")
            logger_provider = logs_api.get_logger_provider()
            logger.debug(f"LoggerProvider type: {type(logger_provider).__name__}")

            # If NoOp LoggerProvider, initialize SDK LoggerProvider
            if not isinstance(logger_provider, LoggerProvider):
                logger.debug("Initializing LoggerProvider (not enabled by auto-instrumentation)")
                logger_provider = LoggerProvider()
                logs_api.set_logger_provider(logger_provider)

            # Attach LoggingHandler to bridge Python logging → OTel logs
            # Deduplicate: keep at most one to avoid log duplication.
            root_logger = python_logging.getLogger()

            def _is_logging_handler(h):
                try:
                    return isinstance(h, LoggingHandler)
                except TypeError:
                    return False

            logging_handlers = [h for h in list(root_logger.handlers) if _is_logging_handler(h)]

            if logging_handlers:
                handler = logging_handlers[0]
                # Remove all existing LoggingHandlers (including the first), then re-add one
                for h in logging_handlers:
                    root_logger.removeHandler(h)
                root_logger.addHandler(handler)
                logger.debug("Reusing existing OTel LoggingHandler on root logger (deduped)")
            else:
                logger.debug("Attaching LoggingHandler to Python logging")
                handler = LoggingHandler(
                    level=python_logging.NOTSET, logger_provider=logger_provider
                )
                root_logger.addHandler(handler)

            handler._clarvynn_logging_bridge = (
                True  # Mark so we can temporarily detach for basicConfig
            )
            _patch_basic_config_for_logging_bridge()

            original_log_processor = None
            active_log_proc = None

            # Try multiple attribute names (OTel SDK version differences)
            for attr_name in ("_active_log_record_processor", "_multi_log_record_processor"):
                if hasattr(logger_provider, attr_name):
                    active_log_proc = getattr(logger_provider, attr_name)
                    logger.debug(f"Found LoggerProvider.{attr_name}")
                    break

            if active_log_proc is None:
                logger.warning("LoggerProvider has no active log processor; cannot intercept")

            if active_log_proc is not None:
                # Try multiple attribute names for the processor list
                log_processors = None
                source_attr = None  # Track which attribute we successfully read from
                for proc_attr in ("_log_record_processors", "_processors"):
                    if hasattr(active_log_proc, proc_attr):
                        try:
                            log_processors = list(getattr(active_log_proc, proc_attr))
                            source_attr = proc_attr  # Remember the source attribute
                            logger.debug(
                                f"Found {len(log_processors)} log processors via {proc_attr}"
                            )
                            break
                        except (TypeError, AttributeError) as e:
                            logger.warning(f"{proc_attr} is not iterable: {e}")

                if log_processors is not None and source_attr is not None:
                    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

                    for p in log_processors:
                        if isinstance(p, BatchLogRecordProcessor):
                            original_log_processor = p
                            break

                    if original_log_processor:
                        log_processors.remove(original_log_processor)
                        # Update the SAME attribute we read from (avoid stale state bug)
                        setattr(active_log_proc, source_attr, tuple(log_processors))
                        logger.debug("✓ Intercepted OTel BatchLogRecordProcessor for logs")
                    else:
                        logger.warning(
                            f"Could not find BatchLogRecordProcessor in {len(log_processors)} processors"
                        )
                else:
                    logger.warning(
                        "Active log processor has no _log_record_processors; cannot intercept"
                    )

            from clarvynn.processors.batch_exporter_adapter import (
                ProcessorToLogExporterAdapter,
            )

            if original_log_processor:
                log_exporter = ProcessorToLogExporterAdapter(original_log_processor)

                # If we intercepted a processor, we already have async behavior.
                async_log_exporter = log_exporter

                # Create Clarvynn log processor (shares trace decision cache and log buffer)
                logger.debug("Creating ClarvynnLogProcessor")
                log_processor = ClarvynnLogProcessor(
                    adapter, async_log_exporter, span_processor, log_buffer=log_buffer
                )

                # Add log processor to logger provider
                logger.debug("Adding log processor to LoggerProvider")
                logger_provider.add_log_record_processor(log_processor)

                # CRITICAL: Pass the log exporter to the SpanProcessor so it can flush buffered logs
                span_processor.log_exporter = async_log_exporter

                logger.info("Log processor initialized")
            else:
                # IMPORTANT: If we couldn't intercept OTel's existing processor, do NOT add
                # our own exporter. That would cause double log exports (OTel's + ours).
                # Instead, skip log filtering and let OTel handle logs natively.
                logger.warning(
                    "Could not intercept OTel log processor - skipping Clarvynn log filtering "
                    "to avoid duplicate exports. Logs will be exported via OTel's native pipeline."
                )

        except ImportError as e:
            logger.warning(f"Could not set up log filtering: {e}")
            logger.warning("Logs will be exported without filtering")

        except Exception as e:
            logger.warning(f"Log filtering setup failed: {e}")
            logger.warning("Logs will be exported without filtering")
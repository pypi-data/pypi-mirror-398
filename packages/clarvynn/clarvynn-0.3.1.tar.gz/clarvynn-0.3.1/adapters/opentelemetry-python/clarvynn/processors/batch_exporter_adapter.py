"""
Adapter classes for bridging OTel Processors to Exporter interfaces.

These adapters intercept OTel's auto-configured BatchSpanProcessor/
BatchLogRecordProcessor and reuse them downstream, preserving user
configuration (endpoints, headers, etc.).
"""

from typing import Any, Sequence, Union

from opentelemetry.sdk._logs import LogRecordProcessor
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, LogExporter, LogExportResult
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

# Handle OTel SDK version differences (1.39 removed LogData)
try:
    from opentelemetry.sdk._logs import ReadableLogRecord

    OTEL_139_PLUS = True
    # Type alias for log records across SDK versions
    LogRecordType = ReadableLogRecord
except ImportError:
    from opentelemetry.sdk._logs import LogData

    OTEL_139_PLUS = False
    LogRecordType = LogData  # type: ignore[misc]


class ProcessorToExporterAdapter(SpanExporter):
    """
    Adapts a SpanProcessor to the SpanExporter interface.

    This lets us "steal" the processor that OTel auto-configured
    (usually BatchSpanProcessor) and plug it downstream of Clarvynn
    as if it were a normal exporter.
    """

    def __init__(self, processor: SpanProcessor):
        self.processor = processor

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Delegate export to the underlying processor's on_end."""
        for span in spans:
            self.processor.on_end(span)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self.processor.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self.processor.force_flush(timeout_millis)


class ProcessorToLogExporterAdapter(LogExporter):
    """
    Adapts a LogRecordProcessor to the LogExporter interface.

    This lets us reuse the log processor that OTel auto-configured (usually
    BatchLogRecordProcessor) as the downstream exporter in Clarvynn's pipeline.
    """

    def __init__(self, processor: LogRecordProcessor):
        self.processor = processor

    def export(self, batch: Sequence[Any]) -> LogExportResult:
        """Delegate export to the underlying processor's on_emit/emit."""
        for log_record in batch:
            # Handle both old (emit) and new (on_emit) method names for SDK compatibility
            if hasattr(self.processor, "on_emit"):
                self.processor.on_emit(log_record)
            else:
                self.processor.emit(log_record)
        return LogExportResult.SUCCESS

    def shutdown(self) -> None:
        self.processor.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self.processor.force_flush(timeout_millis)


class BatchLogExporterAdapter(LogExporter):
    """
    Wraps a LogExporter with BatchLogRecordProcessor for async batching.

    Used when we can't intercept OTel's auto-configured processor and need
    to build our own exporter from environment settings.
    """

    def __init__(self, exporter: LogExporter):
        self._inner_processor = BatchLogRecordProcessor(exporter)

    def export(self, batch: Sequence[Any]) -> LogExportResult:
        """Queue logs for export via BatchLogRecordProcessor."""
        for log_record in batch:
            if hasattr(self._inner_processor, "on_emit"):
                self._inner_processor.on_emit(log_record)
            else:
                self._inner_processor.emit(log_record)
        return LogExportResult.SUCCESS

    def shutdown(self) -> None:
        self._inner_processor.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._inner_processor.force_flush(timeout_millis)


class NoOpLogExporter(LogExporter):
    """
    A no-operation log exporter that discards all logs.

    Used when OTEL_LOGS_EXPORTER=none. Logs are still filtered by Clarvynn,
    but not exported anywhere.
    """

    def export(self, batch: Sequence[Any]) -> LogExportResult:
        """Discard logs and return success."""
        return LogExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

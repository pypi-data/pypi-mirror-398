"""
ClarvynnTraceStateExporter - W3C TraceContext Level 2 Support

This exporter wraps the OTLP exporter and injects W3C TraceState into spans
before export, enabling distributed tracing with critical trace propagation.

KEY INSIGHT: ReadableSpan is immutable, but we can create new span objects
during export with modified TraceState. This allows us to:
- Mark critical traces with ot=th:0 (forces 100% downstream sampling)
- Propagate base_rate thresholds for consistent sampling
- Ensure complete traces when errors occur across services
"""

import logging
from typing import Sequence

from opentelemetry.sdk.trace import ReadableSpan, _Span
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import SpanContext, TraceState

logger = logging.getLogger(__name__)


class ClarvynnTraceStateExporter(SpanExporter):
    """
    Wrapper exporter that injects W3C TraceState before forwarding to OTLP.

    This enables distributed tracing by propagating sampling decisions:
    - Critical traces (errors/slow): ot=th:0 (100% downstream sampling)
    - Base rate traces: ot=th:XXX (consistent sampling across services)

    ARCHITECTURE: Sits between ClarvynnSpanProcessor and OTLPSpanExporter
    """

    def __init__(self, base_exporter: SpanExporter, adapter):
        """
        Initialize TraceState exporter wrapper.

        Args:
            base_exporter: OTLP exporter to forward spans to
            adapter: ProductionCPLAdapter for policy access
        """
        self.base_exporter = base_exporter
        self.adapter = adapter
        self.stats = {
            "critical_traces": 0,
            "base_rate_traces": 0,
            "total_exports": 0,
        }
        logger.info("ClarvynnTraceStateExporter initialized (W3C TraceContext Level 2)")

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """
        Export spans with TraceState injection.

        W3C TraceContext Level 2 Compliance:
        1. If span has upstream TraceState: PRESERVE IT (don't overwrite)
        2. If critical: inject ot=th:0 OR preserve upstream ot=th:0
        3. If base rate: inject our threshold only if no upstream threshold
        4. MERGE with existing TraceState (preserve other vendors)

        Args:
            spans: List of spans to export

        Returns:
            SpanExportResult from base exporter
        """
        self.stats["total_exports"] += 1

        if not spans:
            return self.base_exporter.export(spans)

        modified_spans = []

        for span in spans:
            is_critical = self._is_critical_span(span)
            has_upstream = self._has_upstream_tracestate(span)

            if is_critical:
                # Critical span: inject or preserve ot=th:0
                new_span = self._inject_critical_tracestate(span)
                modified_spans.append(new_span)
                self.stats["critical_traces"] += 1
                logger.debug(f"Injected ot=th:0 for critical span: {span.name}")
            elif has_upstream:
                # Preserve upstream TraceState (don't overwrite)
                # This span was exported because upstream wanted it
                modified_spans.append(span)
                logger.debug(f"Preserving upstream TraceState for span: {span.name}")
            else:
                # Our base rate decision: inject our threshold
                new_span = self._inject_base_rate_tracestate(span)
                modified_spans.append(new_span)
                self.stats["base_rate_traces"] += 1
                logger.debug(f"Injected base rate threshold for span: {span.name}")

        return self.base_exporter.export(modified_spans)

    def _is_critical_span(self, span: ReadableSpan) -> bool:
        """
        Determine if span should be marked as critical.

        A span is critical if:
        1. CPL condition triggered (error, slow, custom condition)
        2. Marked by ClarvynnSpanProcessor via attribute

        Returns:
            True if span should force 100% downstream sampling
        """
        if span.attributes is None:
            # Should not happen for ReadableSpan, but safe guard
            return False

        # Check if processor marked this as critical
        if span.attributes.get("clarvynn.critical") is True:
            return True

        # Re-evaluate CPL conditions to be safe
        attrs = dict(span.attributes)
        attrs["span.name"] = span.name

        if span.status:
            attrs["status_code"] = span.status.status_code.value

        if span.start_time and span.end_time:
            duration_ms = (span.end_time - span.start_time) / 1_000_000
            attrs["duration"] = duration_ms

        for condition in self.adapter.get_conditions():
            if condition.evaluate(attrs):
                return True

        return False

    def _has_upstream_tracestate(self, span: ReadableSpan) -> bool:
        """
        Check if span has upstream TraceState with ot vendor key.

        Returns:
            True if upstream already set TraceState
        """
        try:
            trace_state = span.context.trace_state
            if not trace_state:
                return False

            # Check if OpenTelemetry vendor key exists
            ot_value = trace_state.get("ot")
            return ot_value is not None and ot_value.startswith("th:")

        except (AttributeError, ValueError):
            return False

    def _inject_critical_tracestate(self, span: ReadableSpan) -> ReadableSpan:
        """
        Create new span with ot=th:0 TraceState (100% sampling).

        W3C Compliance: MERGES with existing TraceState entries.
        Preserves other vendor entries while updating ot vendor key.

        Args:
            span: Original span

        Returns:
            New span with TraceState injected
        """
        # Start with existing TraceState entries
        existing_entries = []
        if span.context.trace_state:
            existing_entries = list(span.context.trace_state.items())

        # Remove existing ot entry (if any)
        existing_entries = [(k, v) for k, v in existing_entries if k != "ot"]

        # Add our critical threshold at the front (per W3C spec)
        new_entries = [("ot", "th:0")] + existing_entries

        # Create merged TraceState
        tracestate = TraceState(new_entries)

        # Create new span context with TraceState
        new_context = SpanContext(
            trace_id=span.context.trace_id,
            span_id=span.context.span_id,
            is_remote=span.context.is_remote,
            trace_flags=span.context.trace_flags,
            trace_state=tracestate,
        )

        # Create modified span with new context
        return self._create_span_with_context(span, new_context)

    def _inject_base_rate_tracestate(self, span: ReadableSpan) -> ReadableSpan:
        """
        Create new span with ot=th:XXX TraceState (base rate threshold).

        W3C Compliance: MERGES with existing TraceState entries.
        This ensures:
        - Consistent sampling across services (10% everywhere)
        - Preserves other vendor metadata
        - No trace fragmentation from independent random decisions

        Args:
            span: Original span

        Returns:
            New span with TraceState injected
        """
        # Calculate threshold from base_rate
        base_rate = self.adapter.get_base_rate()

        if base_rate >= 1.0:
            # 100% sampling = critical threshold
            threshold_hex = "0"
        else:
            # Calculate W3C threshold (56-bit value)
            threshold = int((1.0 - base_rate) * (2**56))
            threshold_hex = format(threshold, "x")

        # Start with existing TraceState entries
        existing_entries = []
        if span.context.trace_state:
            existing_entries = list(span.context.trace_state.items())

        # Remove existing ot entry (if any)
        existing_entries = [(k, v) for k, v in existing_entries if k != "ot"]

        # Add our threshold at the front (per W3C spec)
        new_entries = [("ot", f"th:{threshold_hex}")] + existing_entries

        # Create merged TraceState
        tracestate = TraceState(new_entries)

        # Create new span context with TraceState
        new_context = SpanContext(
            trace_id=span.context.trace_id,
            span_id=span.context.span_id,
            is_remote=span.context.is_remote,
            trace_flags=span.context.trace_flags,
            trace_state=tracestate,
        )

        # Create modified span with new context
        return self._create_span_with_context(span, new_context)

    def _create_span_with_context(
        self, original_span: ReadableSpan, new_context: SpanContext
    ) -> ReadableSpan:
        """
        Create new span with modified context but same data.

        This is the key to export-time TraceState injection:
        - We can't modify ReadableSpan (immutable)
        - But we CAN create new span objects for export
        - OpenTelemetry SDK allows this pattern

        Args:
            original_span: Original immutable span
            new_context: New SpanContext with TraceState

        Returns:
            New ReadableSpan with modified context
        """
        # Most OTLP exporters work with the span's internal representation
        # We need to create a wrapper that presents the new context
        # but delegates everything else to the original span

        return _ModifiedContextSpan(original_span, new_context)

    def shutdown(self):
        """Shutdown the exporter."""
        logger.info("Shutting down ClarvynnTraceStateExporter")
        logger.info(f"  Critical traces exported: {self.stats['critical_traces']}")
        logger.info(f"  Base rate traces exported: {self.stats['base_rate_traces']}")
        logger.info(f"  Total exports: {self.stats['total_exports']}")
        return self.base_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush pending spans."""
        return self.base_exporter.force_flush(timeout_millis)


class _ModifiedContextSpan:
    """
    Wrapper that presents a modified SpanContext but delegates to original span.

    This is the technical solution to the immutability problem:
    - ReadableSpan is immutable (can't modify context)
    - But exporters read span.context to get TraceState
    - So we create a wrapper that returns our modified context
    - But delegates all other attributes to original span
    """

    def __init__(self, original_span: ReadableSpan, new_context: SpanContext):
        self._original = original_span
        self._context = new_context

    @property
    def context(self) -> SpanContext:
        """Return modified context with TraceState."""
        return self._context

    def __getattr__(self, name):
        """Delegate all other attributes to original span."""
        return getattr(self._original, name)

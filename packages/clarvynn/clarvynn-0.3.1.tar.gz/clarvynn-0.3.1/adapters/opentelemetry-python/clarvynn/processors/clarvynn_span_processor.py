"""
ClarvynnSpanProcessor - Deferred Head Sampling Processor for Clarvynn.

This implements OpenTelemetry's SpanProcessor interface and evaluates
CPL policies AFTER spans complete, allowing intelligent decisions based
on actual request outcomes (status_code, duration, errors).

KEY INSIGHT: Unlike Sampler (head-based), SpanProcessor (tail-based)
can see the ACTUAL results of requests, enabling:
- 100% error capture
- 100% slow request capture
- Intelligent filtering based on real outcomes

LOCAL CONTEXT PRESERVATION (Span + Log Buffering):
Both spans and logs are buffered during the request lifecycle. When the
LOCAL ROOT span ends (the entry point span for this service), we make
the final decision based on the accumulated state:

- If ANY span in the trace was critical (CPL triggered) → Export ALL spans + logs
- If NO span was critical, but local root is sampled (base rate) → Export ALL spans + logs
- If NO span was critical AND local root is unsampled (base rate) → Drop ALL spans + logs

This ensures complete local context: either the entire local trace is preserved
or dropped together, preventing partial traces where some child spans are missing.
"""

import threading
import time
from collections import OrderedDict
from typing import Optional

from clarvynn.logging import get_logger
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import SpanKind

logger = get_logger("span_processor")


class ClarvynnSpanProcessor(SpanProcessor):
    """
    Deferred Head Sampling processor that evaluates CPL policies.

    This processor is added to TracerProvider and is called:
    - on_start(): When span starts (we just track it)
    - on_end(): When span completes (THIS IS WHERE WE DECIDE)

    ARCHITECTURE: Mirrors Clarvynn SDK's CPLBatchSpanProcessor
    """

    def __init__(self, adapter, exporter: SpanExporter, log_buffer=None, log_exporter=None):
        """
        Initialize processor with Clarvynn adapter and TraceState exporter.

        Args:
            adapter: ProductionCPLAdapter that evaluates CPL conditions
            exporter: ClarvynnTraceStateExporter (wraps OTLP)
            log_buffer: SharedRingBuffer for Flight Recorder (optional)
            log_exporter: LogExporter to flush buffered logs to (optional)
        """
        self.adapter = adapter
        self.exporter = exporter
        self.log_buffer = log_buffer
        self.log_exporter = log_exporter
        self.stats = {
            "total_spans": 0,
            "exported_spans": 0,
            "dropped_spans": 0,
            "critical_spans": 0,
            "upstream_forced": 0,
            "flushed_logs": 0,
            "cleared_logs": 0,
            "buffered_spans": 0,
            "buffer_overflow": 0,  # Spans exported early due to per-trace limit
            "buffer_evicted": 0,  # Traces evicted early due to buffer full (FIFO)
        }

        # Trace decision cache for log filtering
        # Maps trace_id -> bool (True = exported, False = dropped)
        # Using OrderedDict for LRU-like eviction
        self._trace_decisions = OrderedDict()
        self._max_cache_size = 10000
        self._cache_lock = threading.Lock()  # Protects shared state

        # Critical traces set: tracks trace_ids where ANY span was critical
        # Uses OR logic - once a trace is marked critical, it stays critical
        self._critical_traces = set()

        # Pending spans buffer: holds child spans until local root ends
        # Using OrderedDict for O(1) FIFO eviction (oldest trace first)
        # Maps trace_id -> list of (span, is_critical) tuples
        self._pending_spans = OrderedDict()

        # Timestamps for pending spans (for TTL-based cleanup)
        # Using OrderedDict to maintain insertion order
        # Maps trace_id -> first_buffered_timestamp
        self._pending_timestamps = OrderedDict()

        # Buffer limits (matching log buffer design for consistency)
        self._max_active_traces = 10000  # Max concurrent traces with buffered spans
        self._max_spans_per_trace = 50  # Max child spans per trace (matches typical depth)
        self._buffer_ttl_seconds = 60.0  # Max time before orphan export
        self._cleanup_interval_seconds = 30.0  # Min time between TTL cleanups
        self._last_cleanup_time = time.time()  # Track last cleanup for time-based trigger

        logger.info(
            "ClarvynnSpanProcessor initialized (Deferred Head Sampling + W3C TraceContext Level 2)"
        )
        if self.log_buffer:
            logger.info("Flight Recorder enabled (Span + Log Buffering active)")

    def on_start(self, span: ReadableSpan, parent_context: Optional[Context] = None):
        """
        Called when span starts.

        At this point, the request hasn't executed yet, so we don't
        have status_code, duration, or error information.

        We just track that the span started.
        """
        self.stats["total_spans"] += 1
        logger.debug(f"Span started: {span.name}")

    def on_end(self, span: ReadableSpan):
        """
        Called when span ENDS (request completed).

        For CHILD spans:
        - Evaluate CPL policy to determine criticality
        - Buffer the span until local root decides

        For LOCAL ROOT span:
        - Evaluate CPL policy
        - Make final decision: if trace is critical OR root is sampled,
          export ALL buffered spans + logs; otherwise drop all
        """
        trace_id = span.context.trace_id

        try:
            attrs = self._extract_span_attributes(span)
            logger.debug(
                f"  Extracted attributes: method={attrs.get('method', 'N/A')}, "
                f"path={attrs.get('path', 'N/A')}, status_code={attrs.get('status_code', 'N/A')}, "
                f"duration={attrs.get('duration', 'N/A')}ms"
            )

            should_keep, reason, is_critical = self._should_export_span(span, attrs)

            # Track criticality using OR logic (if any span is critical, trace is critical)
            if is_critical:
                self._mark_trace_critical(trace_id)

            if self._is_local_root_span(span):
                # LOCAL ROOT: finalize the entire trace
                self._finalize_trace(trace_id, span, should_keep, reason, is_critical)
            else:
                # CHILD SPAN: buffer until root decides
                self._buffer_span(trace_id, span, is_critical)

        except Exception as e:
            logger.error(f"Error in span evaluation: {e}")
            # Fail-safe: export this span immediately
            self.exporter.export([span])
            self.stats["exported_spans"] += 1

            # If this is local root, flush everything as fail-safe
            if self._is_local_root_span(span):
                self._finalize_trace_failsafe(trace_id)

    def _buffer_span(self, trace_id: int, span: ReadableSpan, is_critical: bool) -> None:
        """
        Buffer a child span until the local root span ends.

        Enforces capacity limits to prevent OOM:
        - Max active traces: 10,000 (FIFO eviction when full)
        - Max spans per trace: 50 (overflow exports immediately)

        Uses FIFO eviction: when buffer is full, evict oldest trace
        (export all its spans) to make room for new trace.

        Args:
            trace_id: The trace this span belongs to
            span: The span to buffer
            is_critical: Whether this span triggered a CPL condition
        """
        overflow_span = None  # Track overflow for export outside lock

        with self._cache_lock:
            # Check 1: Is this a new trace that needs a buffer slot?
            if trace_id not in self._pending_spans:
                # FIFO eviction: if buffer full, evict oldest trace
                while len(self._pending_spans) >= self._max_active_traces:
                    self._evict_oldest_trace_unlocked()

                # Create new entry for this trace (appended to end of OrderedDict)
                self._pending_spans[trace_id] = []
                self._pending_timestamps[trace_id] = time.time()

            # Check 2: Per-trace span limit
            if len(self._pending_spans[trace_id]) >= self._max_spans_per_trace:
                # Too many child spans - mark for export outside lock
                # IMPORTANT: Mark trace as critical so when root ends, ALL spans export
                # This prevents partial traces (overflow exported, rest dropped)
                self._critical_traces.add(trace_id)
                self.stats["buffer_overflow"] += 1
                overflow_span = span
            else:
                # Normal case: buffer the span
                self._pending_spans[trace_id].append((span, is_critical))
                self.stats["buffered_spans"] += 1
                logger.debug(f"Buffered child span: {span.name}")

        # Process deferred evictions OUTSIDE the lock (avoids blocking)
        self._process_deferred_evictions()

        # Handle overflow span OUTSIDE the lock
        if overflow_span is not None:
            logger.debug(
                f"Trace span limit ({self._max_spans_per_trace}): exporting span immediately (trace marked critical)"
            )
            self.exporter.export([overflow_span])
            self.stats["exported_spans"] += 1

        # Periodic cleanup of expired traces
        # Trigger if: (1) every 100 spans buffered, OR (2) 30s elapsed since last cleanup
        # Time-based trigger ensures cleanup happens even during traffic lulls
        time_since_cleanup = time.time() - self._last_cleanup_time
        if (
            self.stats["buffered_spans"] % 100 == 0
            or time_since_cleanup >= self._cleanup_interval_seconds
        ):
            self._cleanup_expired_traces()
            self._last_cleanup_time = time.time()

    def _evict_oldest_trace_unlocked(self) -> None:
        """
        Evict the oldest buffered trace (FIFO) to make room.

        MUST be called while holding _cache_lock.

        This method only collects data under the lock. The actual export
        happens after the caller releases the lock via _complete_eviction().

        NOTE: Caller must call _complete_eviction() after releasing lock!
        """
        if not self._pending_spans:
            return

        # popitem(last=False) removes and returns the OLDEST entry in O(1)
        oldest_trace_id, buffered_spans = self._pending_spans.popitem(last=False)
        self._pending_timestamps.pop(oldest_trace_id, None)
        was_critical = oldest_trace_id in self._critical_traces
        self._critical_traces.discard(oldest_trace_id)

        # Store for deferred export (after lock released)
        # We append to a list that _buffer_span will process
        if not hasattr(self, "_deferred_evictions"):
            self._deferred_evictions = []
        self._deferred_evictions.append((oldest_trace_id, buffered_spans, was_critical))
        self.stats["buffer_evicted"] += 1

    def _process_deferred_evictions(self) -> None:
        """
        Process any deferred trace evictions OUTSIDE the lock.

        This ensures exports don't block the critical section.
        Called after releasing _cache_lock.

        Note: We acquire the lock briefly to copy and clear the list atomically,
        then release it before doing the actual exports.
        """
        if not hasattr(self, "_deferred_evictions"):
            return

        # Atomically copy and clear under lock to prevent race condition
        with self._cache_lock:
            if not self._deferred_evictions:
                return
            evictions = self._deferred_evictions[:]  # Copy
            self._deferred_evictions.clear()  # Clear atomically

        for trace_id, buffered_spans, was_critical in evictions:
            # Record decision for ClarvynnLogProcessor consistency
            self._record_trace_decision(trace_id, True)  # Eviction = export = True

            # Export all buffered spans
            for buffered_span, span_was_critical in buffered_spans:
                if span_was_critical or was_critical:
                    self._mark_span_critical(buffered_span)
                    self.stats["critical_spans"] += 1
                self.exporter.export([buffered_span])
                self.stats["exported_spans"] += 1

            # Handle log buffer (flush since we're exporting)
            if self.log_buffer:
                self._handle_buffered_logs(trace_id, True)

            if buffered_spans:
                logger.debug(
                    f"FIFO eviction: exported {len(buffered_spans)} spans from oldest trace "
                    f"(buffer at capacity)"
                )

    def _cleanup_expired_traces(self) -> None:
        """
        Export traces that have been buffered too long (TTL exceeded).

        This prevents OOM from orphaned traces where root span never ends,
        such as buggy instrumentation or very long-running requests.

        Properly records trace decision and handles log buffer for consistency.
        """
        now = time.time()
        expired_data = []  # Collect data, export outside lock

        with self._cache_lock:
            for trace_id, first_buffered in list(self._pending_timestamps.items()):
                if now - first_buffered > self._buffer_ttl_seconds:
                    buffered_spans = self._pending_spans.pop(trace_id, [])
                    self._pending_timestamps.pop(trace_id, None)
                    was_critical = trace_id in self._critical_traces
                    self._critical_traces.discard(trace_id)
                    expired_data.append((trace_id, buffered_spans, was_critical))

        # Export expired traces OUTSIDE the lock
        for trace_id, buffered_spans, was_critical in expired_data:
            # Record decision for ClarvynnLogProcessor consistency
            self._record_trace_decision(trace_id, True)  # TTL expiry = export = True

            # Export all buffered spans
            for buffered_span, span_was_critical in buffered_spans:
                if span_was_critical or was_critical:
                    self._mark_span_critical(buffered_span)
                    self.stats["critical_spans"] += 1
                self.exporter.export([buffered_span])
                self.stats["exported_spans"] += 1

            # Handle log buffer (flush since we're exporting)
            if self.log_buffer:
                self._handle_buffered_logs(trace_id, True)

            if buffered_spans:
                logger.warning(
                    f"TTL expired: exported {len(buffered_spans)} orphaned spans "
                    f"(root span never ended for trace)"
                )

    def _finalize_trace(
        self,
        trace_id: int,
        root_span: ReadableSpan,
        root_should_keep: bool,
        root_reason: str,
        root_is_critical: bool,
    ) -> None:
        """
        Finalize the trace when local root span ends.

        Makes the final export/drop decision for ALL local spans + logs based on:
        - If ANY span was critical → Export all
        - If root is sampled (base rate) → Export all
        - Otherwise → Drop all
        """
        # Get the final decision
        trace_is_critical = self._is_trace_critical(trace_id)
        final_decision = trace_is_critical or root_should_keep

        # Record decision for ClarvynnLogProcessor compatibility
        self._record_trace_decision(trace_id, final_decision)

        # Get and clear buffered child spans
        with self._cache_lock:
            buffered_spans = self._pending_spans.pop(trace_id, [])
            self._pending_timestamps.pop(trace_id, None)  # Clean up timestamp

        if final_decision:
            # EXPORT: All buffered child spans + root span
            critical_count = 0

            for buffered_span, was_critical in buffered_spans:
                if was_critical:
                    self._mark_span_critical(buffered_span)
                    critical_count += 1
                self.exporter.export([buffered_span])
                self.stats["exported_spans"] += 1

            # Export root span
            if root_is_critical or trace_is_critical:
                self._mark_span_critical(root_span)
                critical_count += 1
            self.exporter.export([root_span])
            self.stats["exported_spans"] += 1
            self.stats["critical_spans"] += critical_count

            self._log_export_reason(root_span, root_reason, len(buffered_spans) + 1)
        else:
            # DROP: All spans (root + buffered children)
            dropped_count = len(buffered_spans) + 1  # +1 for root
            self.stats["dropped_spans"] += dropped_count
            logger.debug(f"🗑️ Dropped {dropped_count} spans for trace")

        # Handle buffered logs
        if self.log_buffer:
            self._handle_buffered_logs(trace_id, final_decision)

        # Cleanup
        self._cleanup_trace_criticality(trace_id)

    def _finalize_trace_failsafe(self, trace_id: int) -> None:
        """
        Emergency finalization when an error occurs during processing.

        Fail-safe: export all buffered spans and logs to avoid data loss.
        """
        with self._cache_lock:
            buffered_spans = self._pending_spans.pop(trace_id, [])
            self._pending_timestamps.pop(trace_id, None)  # Fix: clean up timestamp

        # Export all buffered spans
        for buffered_span, _ in buffered_spans:
            self.exporter.export([buffered_span])
            self.stats["exported_spans"] += 1

        # Flush logs
        if self.log_buffer:
            self._handle_buffered_logs(trace_id, True)

        self._cleanup_trace_criticality(trace_id)
        logger.warning(f"Fail-safe: exported {len(buffered_spans)} buffered spans due to error")

    def _is_local_root_span(self, span: ReadableSpan) -> bool:
        """
        Check if this span is the local root for this service.

        Local root = entry point span for this service instance.
        It may have a remote parent (from upstream service), but no local parent.

        Detection strategy:
        1. SERVER spans are always local roots (HTTP/gRPC entry points)
        2. CONSUMER spans are local roots (message queue consumers)
        3. Spans with no parent are true roots
        4. Spans with remote parent are local roots
        """
        # SERVER and CONSUMER spans are entry points to this service
        if span.kind in (SpanKind.SERVER, SpanKind.CONSUMER):
            return True

        # Check if span has no parent (true root of entire trace)
        if span.parent is None:
            return True

        # Check if parent is remote (from another service)
        # Remote parent means this is a local root
        if hasattr(span.parent, "is_remote") and span.parent.is_remote is True:
            return True

        return False

    def _mark_trace_critical(self, trace_id: int) -> None:
        """Mark a trace as critical. Uses OR logic - once critical, stays critical."""
        with self._cache_lock:
            self._critical_traces.add(trace_id)

    def _is_trace_critical(self, trace_id: int) -> bool:
        """Check if any span in this trace was marked critical."""
        with self._cache_lock:
            return trace_id in self._critical_traces

    def _cleanup_trace_criticality(self, trace_id: int) -> None:
        """Remove trace from critical set after local root ends."""
        with self._cache_lock:
            self._critical_traces.discard(trace_id)

    def _log_export_reason(self, span: ReadableSpan, reason: str, span_count: int = 1) -> None:
        """Log the export decision with appropriate detail level."""
        if span_count > 1:
            suffix = f" ({span_count} spans in trace)"
        else:
            suffix = ""

        if reason.startswith("condition:"):
            logger.info(
                f"✅ CPL condition '{reason}' triggered - exporting critical trace: {span.name}{suffix}"
            )
        elif reason == "upstream_critical":
            logger.info(f"✅ Upstream critical trace (ot=th:0) - exporting: {span.name}{suffix}")
        elif reason == "upstream_threshold":
            logger.info(f"✅ Upstream threshold match - exporting: {span.name}{suffix}")
        else:
            logger.info(f"✅ Exported trace: {span.name} (reason: {reason}){suffix}")

    def _handle_buffered_logs(self, trace_id: int, should_keep: bool) -> None:
        """
        Flush or clear buffered logs for the given trace.

        Called only when local root span ends, ensuring all child spans
        have had a chance to mark the trace as critical.
        """
        if trace_id == 0:
            return

        if should_keep:
            logs = self.log_buffer.get_and_clear(trace_id)
            if logs and self.log_exporter is not None:
                self.log_exporter.export(logs)
                self.stats["flushed_logs"] += len(logs)
                logger.debug(f"Flushed {len(logs)} buffered logs for trace")
        else:
            logs = self.log_buffer.get_and_clear(trace_id)
            if logs:
                self.stats["cleared_logs"] += len(logs)
                logger.debug(f"Cleared {len(logs)} buffered logs for trace")

    def _extract_span_attributes(self, span: ReadableSpan) -> dict:
        """
        Extract complete attributes from finished span.

        Returns:
            dict with all attributes needed for CPL evaluation
        """
        attrs = {}

        if span.attributes:
            attrs.update(dict(span.attributes))

        attrs["span.name"] = span.name
        attrs["trace_id"] = span.context.trace_id

        if span.status:
            attrs["status_code"] = span.status.status_code.value

        if span.start_time and span.end_time:
            duration_ms = (span.end_time - span.start_time) / 1_000_000
            attrs["duration"] = duration_ms
            attrs["duration_ms"] = duration_ms  # CPL uses duration_ms

        if "http.status_code" in attrs:
            attrs["status_code"] = attrs["http.status_code"]

        if "http.route" in attrs:
            attrs["path"] = attrs["http.route"]

        if "http.target" in attrs and "path" not in attrs:
            attrs["path"] = attrs["http.target"]

        if "http.method" in attrs:
            attrs["method"] = attrs["http.method"]

        if "http.url" in attrs and "path" not in attrs:
            # Extract path from full URL
            from urllib.parse import urlparse

            parsed = urlparse(attrs["http.url"])
            attrs["path"] = parsed.path

        return attrs

    def _should_export_span(self, span: ReadableSpan, attrs: dict) -> tuple:
        """
        Evaluate CPL policy to decide if span should be exported.

        W3C TraceContext Level 2 Priority Order:
        1. CPL conditions (errors, slow, critical paths) → ALWAYS export + mark critical
        2. Upstream TraceState (distributed consistency):
           - ot=th:0 → Force export + mark critical
           - ot=th:XXX → Compare with our threshold
        3. Base rate (random sampling) → Export X% of remaining

        Returns:
            (should_export: bool, reason: str, is_critical: bool)
        """

        # Priority 1: CPL Conditions (highest priority)
        for condition in self.adapter.get_conditions():
            if condition.evaluate(attrs):
                return (True, f"condition:{condition.name}", True)

        # Priority 2: Upstream TraceState
        upstream_threshold = self._read_upstream_threshold(span)

        if upstream_threshold is not None:
            if upstream_threshold == 0:
                # Critical trace from upstream (ot=th:0)
                # Force 100% sampling and mark as critical
                self.stats["upstream_forced"] += 1
                return (True, "upstream_critical", True)

            # Check if trace_id passes upstream threshold
            trace_id = attrs.get("trace_id", 0)
            R = trace_id & 0xFFFFFFFFFFFFFF  # Last 56 bits

            if upstream_threshold <= R:
                # Upstream wants this sampled
                return (True, "upstream_threshold", False)

        # Priority 3: Our base rate
        trace_id = attrs.get("trace_id", 0)

        if self._check_base_rate(trace_id):
            return (True, "base_rate", False)

        return (False, "dropped", False)

    def _read_upstream_threshold(self, span: ReadableSpan) -> Optional[int]:
        """
        Read W3C TraceContext Level 2 threshold from upstream service.

        Checks the span's context for TraceState with OpenTelemetry vendor key:
        - ot=th:0 → Critical trace (100% sampling)
        - ot=th:XXX → Threshold value for consistent sampling

        Returns:
            Threshold as integer (0 for critical), or None if not set
        """
        try:
            trace_state = span.context.trace_state

            if not trace_state:
                return None

            # Get OpenTelemetry vendor key value
            ot_value = trace_state.get("ot")

            if not ot_value:
                return None

            # Parse threshold: "th:0" or "th:e666666666666"
            if not ot_value.startswith("th:"):
                return None

            threshold_hex = ot_value[3:]  # Remove "th:" prefix

            if not threshold_hex:
                return None

            # Convert hex to integer
            threshold = int(threshold_hex, 16)

            logger.debug(f"Upstream threshold: {threshold_hex} ({threshold})")
            return threshold

        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse upstream threshold: {e}")
            return None

    def _mark_span_critical(self, span: ReadableSpan):
        """
        Mark span as critical for TraceState injection.

        The TraceStateExporter will read this attribute and inject
        ot=th:0 to force 100% downstream sampling.

        NOTE: We can't modify ReadableSpan directly, but we CAN set
        attributes on the underlying span if it's still mutable.
        For export-only marking, the exporter will re-evaluate conditions.
        """
        # Try to mark the span if it's still mutable (unlikely in on_end)
        # The exporter will re-evaluate CPL conditions to be safe
        try:
            if hasattr(span, "set_attribute"):
                span.set_attribute("clarvynn.critical", True)
        except Exception:
            # Expected - ReadableSpan is immutable
            # Exporter will re-evaluate conditions
            pass

    def _check_base_rate(self, trace_id: int) -> bool:
        """
        Check if trace_id passes base rate sampling.

        Uses W3C TraceContext Level 2 compliant sampling:
        - Extract last 56 bits of trace_id (random)
        - Compare with threshold derived from base_rate
        """
        base_rate = self.adapter.get_base_rate()

        if base_rate >= 1.0:
            return True
        if base_rate <= 0.0:
            return False

        R = trace_id & 0xFFFFFFFFFFFFFF
        T = int((1.0 - base_rate) * (2**56))

        return T <= R

    def _record_trace_decision(self, trace_id: int, was_exported: bool):
        """
        Record whether a trace was exported or dropped.

        This cache is used by ClarvynnLogProcessor to filter logs
        based on trace sampling decisions, ensuring logs and traces
        are consistently sampled together.

        Args:
            trace_id: OpenTelemetry trace ID
            was_exported: True if trace was exported, False if dropped
        """
        with self._cache_lock:
            # Add to cache (OrderedDict maintains insertion order)
            self._trace_decisions[trace_id] = was_exported

            # Evict oldest 10% if cache is full (LRU-like behavior)
            if len(self._trace_decisions) > self._max_cache_size:
                evict_count = self._max_cache_size // 10
                for _ in range(evict_count):
                    self._trace_decisions.popitem(last=False)  # Remove oldest
                logger.debug(f"Evicted {evict_count} old trace decisions from cache")

    def was_trace_exported(self, trace_id: int) -> Optional[bool]:
        """
        Check if a trace was exported or dropped.

        Used by ClarvynnLogProcessor to filter logs based on trace decisions.

        Args:
            trace_id: OpenTelemetry trace ID

        Returns:
            True if trace was exported
            False if trace was dropped
            None if trace_id not in cache (trace not yet processed)
        """
        with self._cache_lock:
            return self._trace_decisions.get(trace_id)

    def shutdown(self):
        """Shutdown the processor."""
        logger.info("Shutting down ClarvynnSpanProcessor")
        logger.info(f"  Trace decision cache size: {len(self._trace_decisions)}")
        logger.info(f"  Buffered spans processed: {self.stats['buffered_spans']}")
        if self.log_buffer:
            logger.info(f"  Flushed logs: {self.stats['flushed_logs']}")
            logger.info(f"  Cleared logs: {self.stats['cleared_logs']}")

        # Export any orphaned buffered spans as fail-safe
        # Collect data under lock, export outside
        orphaned_data = []
        with self._cache_lock:
            for trace_id, spans in list(self._pending_spans.items()):
                was_critical = trace_id in self._critical_traces
                orphaned_data.append((trace_id, spans, was_critical))
            # Clear all state
            self._pending_spans.clear()
            self._pending_timestamps.clear()
            self._critical_traces.clear()

        # Export orphans and handle logs OUTSIDE the lock
        orphaned_count = 0
        for trace_id, spans, was_critical in orphaned_data:
            # Record decision for log processor
            self._record_trace_decision(trace_id, True)  # Shutdown = export = True

            # Export all spans
            for span, span_was_critical in spans:
                if span_was_critical or was_critical:
                    self._mark_span_critical(span)
                    self.stats["critical_spans"] += 1
                self.exporter.export([span])
                orphaned_count += 1

            # Flush logs for this trace
            if self.log_buffer:
                self._handle_buffered_logs(trace_id, True)

        if orphaned_count > 0:
            logger.warning(f"  Exported {orphaned_count} orphaned buffered spans during shutdown")

        self.exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000):
        """
        Force flush pending spans and logs.

        Exports all buffered child spans and flushes corresponding logs.
        Unlike shutdown(), does not clear state (more spans may arrive after flush).
        """
        logger.info("Force flushing spans")

        # Collect buffered data under lock
        flush_data = []
        with self._cache_lock:
            for trace_id, spans in list(self._pending_spans.items()):
                was_critical = trace_id in self._critical_traces
                flush_data.append((trace_id, list(spans), was_critical))
            # Clear span buffers (but leave timestamps for future spans)
            self._pending_spans.clear()

        # Export buffered spans and flush logs OUTSIDE the lock
        flushed_count = 0
        for trace_id, spans, was_critical in flush_data:
            # Record decision for log processor
            self._record_trace_decision(trace_id, True)

            # Export all spans
            for span, span_was_critical in spans:
                if span_was_critical or was_critical:
                    self._mark_span_critical(span)
                    self.stats["critical_spans"] += 1
                self.exporter.export([span])
                flushed_count += 1

            # Flush logs for this trace
            if self.log_buffer:
                self._handle_buffered_logs(trace_id, True)

        if flushed_count > 0:
            logger.info(f"Force flushed {flushed_count} buffered spans")

        return self.exporter.force_flush(timeout_millis)

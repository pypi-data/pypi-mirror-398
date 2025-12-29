"""
SharedRingBuffer - High-Performance Ring Buffer for Flight Recorder

This module implements a shared ring buffer for holding logs during a request.
It uses Lock Striping (Sharding) to minimize contention in high-concurrency environments.

Key Features:
- Sharded Storage: 16 independent segments (locks) to reduce contention.
- Ring Buffer: Uses collections.deque(maxlen=N) to automatically drop OLDEST logs.
- Performance: Atomic operations on segments.

COMPATIBILITY:
- OTel SDK 1.20-1.38: Buffers LogData wrappers
- OTel SDK 1.39+: Buffers ReadableLogRecord directly
"""

import collections
import threading
import time
from typing import Any, Deque, Dict, List, Tuple

from clarvynn.logging import get_logger

logger = get_logger("log_buffer")


class BufferSegment:
    """
    Internal segment for SharedRingBuffer.
    Protects a subset of traces with its own lock.
    """

    def __init__(self, max_capacity: int, max_logs: int):
        self.lock = threading.Lock()
        # trace_id -> (last_access_time, deque)
        self.buffers: Dict[int, Tuple[float, Deque[Any]]] = {}
        self.max_capacity = max_capacity
        self.max_logs = max_logs
        self.op_count = 0


class SharedRingBuffer:
    """
    A thread-safe, sharded ring buffer for storing logs associated with active traces.
    Replaces global locking with segment-based locking (Striping).
    """

    def __init__(
        self,
        max_logs_per_trace: int = 100,
        max_active_traces: int = 10000,
        ttl_seconds: int = 300,
        concurrency_level: int = 16,
    ):
        """
        Initialize the sharded buffer.

        Args:
            max_logs_per_trace: Maximum number of logs per trace.
            max_active_traces: Total maximum active traces (approximate).
            ttl_seconds: Cleanup TTL.
            concurrency_level: Number of lock shards (default 16).
        """
        self._segment_count = concurrency_level
        self._ttl_seconds = ttl_seconds

        # Distribute capacity across segments
        segment_capacity = max(1, max_active_traces // concurrency_level)
        self._segments = [
            BufferSegment(segment_capacity, max_logs_per_trace) for _ in range(concurrency_level)
        ]

        self._cleanup_interval = 100  # Ops per segment before cleanup check

    def _get_segment(self, trace_id: int) -> BufferSegment:
        # Simple modulo hashing
        return self._segments[hash(trace_id) % self._segment_count]

    def add_log(self, trace_id: int, log_record: Any) -> bool:
        """
        Add a log record to the buffer for the given trace_id.
        """
        if not trace_id:
            return False

        current_time = time.time()
        segment = self._get_segment(trace_id)

        with segment.lock:
            # Periodic cleanup (per segment)
            segment.op_count += 1
            if segment.op_count >= self._cleanup_interval:
                segment.op_count = 0
                self._cleanup_segment(segment, current_time)

            if trace_id in segment.buffers:
                # Update timestamp and append
                _, buffer = segment.buffers[trace_id]
                segment.buffers[trace_id] = (current_time, buffer)
                buffer.append(log_record)
                return True
            else:
                # New buffer needed
                if len(segment.buffers) >= segment.max_capacity:
                    # Try one last cleanup before rejecting
                    self._cleanup_segment(segment, current_time)
                    if len(segment.buffers) >= segment.max_capacity:
                        return False

                buffer = collections.deque(maxlen=segment.max_logs)
                buffer.append(log_record)
                segment.buffers[trace_id] = (current_time, buffer)
                return True

    def get_and_clear(self, trace_id: int) -> List[Any]:
        """
        Retrieve buffered logs for a trace and clear the buffer.
        """
        if not trace_id:
            return []

        segment = self._get_segment(trace_id)
        with segment.lock:
            if trace_id in segment.buffers:
                _, buffer = segment.buffers.pop(trace_id)
                return list(buffer)
            return []

    def clear(self, trace_id: int) -> None:
        """
        Clear buffered logs for a trace.
        """
        if not trace_id:
            return

        segment = self._get_segment(trace_id)
        with segment.lock:
            if trace_id in segment.buffers:
                del segment.buffers[trace_id]

    def get_stats(self) -> Dict[str, int]:
        """
        Get global stats (aggregated across segments).
        """
        total_active = 0
        total_logs = 0

        # Note: This is not an atomic snapshot, but sufficient for stats
        for segment in self._segments:
            with segment.lock:
                total_active += len(segment.buffers)
                total_logs += sum(len(buf[1]) for buf in segment.buffers.values())

        return {"active_traces": total_active, "total_buffered_logs": total_logs}

    def _cleanup_segment(self, segment: BufferSegment, current_time: float):
        """
        Remove stale buffers from a specific segment.
        Must be called with segment lock held.
        """
        stale_keys = []
        for tid, (last_access, _) in segment.buffers.items():
            if current_time - last_access > self._ttl_seconds:
                stale_keys.append(tid)

        for tid in stale_keys:
            del segment.buffers[tid]

        if stale_keys:
            logger.debug(f"Cleaned up {len(stale_keys)} stale trace buffers in segment")

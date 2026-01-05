import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict


@dataclass
class MetricsSnapshot:
    request_count: int
    avg_latency_ms: float
    llm_calls: int
    tool_calls: int
    tool_failures: int


_lock = Lock()
_request_count = 0
_latency_total_ms = 0.0
_llm_calls = 0
_tool_calls = 0
_tool_failures = 0


def record_request(latency_ms: float) -> None:
    global _request_count, _latency_total_ms
    with _lock:
        _request_count += 1
        _latency_total_ms += latency_ms


def record_llm_call() -> None:
    global _llm_calls
    with _lock:
        _llm_calls += 1


def record_tool_call(success: bool) -> None:
    global _tool_calls, _tool_failures
    with _lock:
        _tool_calls += 1
        if not success:
            _tool_failures += 1


def snapshot() -> MetricsSnapshot:
    with _lock:
        avg_latency = (_latency_total_ms / _request_count) if _request_count else 0.0
        return MetricsSnapshot(
            request_count=_request_count,
            avg_latency_ms=round(avg_latency, 2),
            llm_calls=_llm_calls,
            tool_calls=_tool_calls,
            tool_failures=_tool_failures,
        )


def as_dict() -> Dict[str, float]:
    snap = snapshot()
    return {
        "request_count": snap.request_count,
        "avg_latency_ms": snap.avg_latency_ms,
        "llm_calls": snap.llm_calls,
        "tool_calls": snap.tool_calls,
        "tool_failures": snap.tool_failures,
    }


def reset_metrics() -> None:
    global _request_count, _latency_total_ms, _llm_calls, _tool_calls, _tool_failures
    with _lock:
        _request_count = 0
        _latency_total_ms = 0.0
        _llm_calls = 0
        _tool_calls = 0
        _tool_failures = 0

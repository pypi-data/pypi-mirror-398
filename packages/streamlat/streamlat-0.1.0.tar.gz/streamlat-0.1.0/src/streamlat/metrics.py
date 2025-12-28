import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


def _now_ns() -> int:
    return time.perf_counter_ns()


def _ns_to_ms(ns: int) -> float:
    return ns / 1_000_000.0


@dataclass
class StreamMetrics:
    ttft_ms: Optional[float]
    e2e_ms: float
    stream_text_ms: Optional[float]
    event_count: int
    text_event_count: int
    output_chars: int
    tokens_est: Optional[int]
    tokens_per_sec_est: Optional[float]


class StreamMetricsCollector:
    """
    Minimal-overhead streaming metrics collector.
    O(1) per event.
    """

    def __init__(self) -> None:
        self.t0_ns = None
        self.t_first_text_ns = None
        self.t_last_text_ns = None
        self.t_done_ns = None

        self.event_count = 0
        self.text_event_count = 0
        self.output_chars = 0

    def on_request_start(self) -> None:
        self.t0_ns = _now_ns()

    def on_event(self) -> None:
        self.event_count += 1

    def on_text(self, text: str) -> None:
        if not text:
            return

        now = _now_ns()
        if self.t_first_text_ns is None:
            self.t_first_text_ns = now

        self.t_last_text_ns = now
        self.text_event_count += 1
        self.output_chars += len(text)

    def on_done(self) -> None:
        self.t_done_ns = _now_ns()

    def finalize(self, output_text: str = "", chars_per_token: int = 4) -> StreamMetrics:
        if self.t0_ns is None:
            self.t0_ns = _now_ns()

        if self.t_done_ns is None:
            self.t_done_ns = _now_ns()

        ttft = None
        if self.t_first_text_ns is not None:
            ttft = _ns_to_ms(self.t_first_text_ns - self.t0_ns)

        stream_text_ms = None
        if self.t_first_text_ns is not None and self.t_last_text_ns is not None:
            stream_text_ms = _ns_to_ms(self.t_last_text_ns - self.t_first_text_ns)

        e2e = _ns_to_ms(self.t_done_ns - self.t0_ns)

        tokens_est = None
        tps_est = None

        if output_text:
            tokens_est = max(1, len(output_text) // chars_per_token)
            if self.t_first_text_ns is not None:
                dur_s = (self.t_done_ns - self.t_first_text_ns) / 1_000_000_000
                if dur_s > 0:
                    tps_est = tokens_est / dur_s

        return StreamMetrics(
            ttft_ms=ttft,
            e2e_ms=e2e,
            stream_text_ms=stream_text_ms,
            event_count=self.event_count,
            text_event_count=self.text_event_count,
            output_chars=len(output_text) if output_text else self.output_chars,
            tokens_est=tokens_est,
            tokens_per_sec_est=tps_est,
        )

    def to_dict(self, m: StreamMetrics) -> Dict[str, Any]:
        return asdict(m)

# streamlat

Tiny utility to measure latency for SSE streaming responses.

Metrics:
- TTFT (time to first text)
- End-to-end latency (request start to stream done)
- Stream text time (first text to last text)
- Event and text event counts
- Estimated token throughput (optional)

## Install
```bash
pip install streamlat

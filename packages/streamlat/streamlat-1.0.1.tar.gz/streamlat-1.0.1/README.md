# streamlat

**streamlat** is a tiny, zero-dependency utility for measuring **latency and throughput of streaming LLM responses**.

It is designed for **SSE-style streaming** and works cleanly with:
- Raw OpenAI structure streaming
- SDK abstractions (LangChain, Microsoft Agent Framework)

No SDK internals. No monkey-patching. Just timestamp hooks.

---

## What it measures

`streamlat` focuses on metrics that actually matter for streaming UX:

- **TTFT (Time to First Token)**  
  Time from request start until the first text chunk is received.

- **End-to-End Latency (E2E)**  
  Time from request start until the stream completes.

- **Stream Text Time**  
  Time between the first and last streamed text chunks.

- **Event Count**  
  Number of streamed chunks/events received.

- **Text Event Count**  
  Number of chunks that actually carried text.

- **Estimated Throughput**  
  Tokens per second (estimated from output length).

All metrics are computed **client-side**, with **O(1) overhead per streamed chunk**.

---

## How it works under the hood

`streamlat` does **not** intercept network traffic.

Instead, you explicitly mark four points in your streaming loop:

1. Request start
2. Each streamed event
3. Each streamed text chunk
4. Stream completion

Internally it:
- Uses `time.perf_counter_ns()` for high-resolution timing
- Stores only timestamps and counters
- Performs no tokenization in the hot path
- Estimates tokens only once at the end

This makes it safe for:
- Production services
- Benchmarks
- Demos
- Framework-based SDKs

---

## Install

```bash
pip install streamlat
```

### Example 1: LangChain (AzureChatOpenAI streaming)

```python
import asyncio
import os

from langchain_openai import AzureChatOpenAI
from streamlat import StreamMetricsCollector


async def main():
    metrics = StreamMetricsCollector()

    llm = AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_deployment="gpt-5",
        api_version="2024-02-15-preview",
        streaming=True,
    )

    metrics.on_request_start()
    output = ""

    async for chunk in llm.astream("Explain SSE streaming in one paragraph."):
        metrics.on_event()
        text = getattr(chunk, "content", "") or ""
        if text:
            metrics.on_text(text)
            output += text
            print(text, end="", flush=True)

    metrics.on_done()

    m = metrics.finalize(output_text=output)
    print("\nMETRICS:")
    for k, v in metrics.to_dict(m).items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Microsoft Agent Framework (Azure OpenAI Assistants)

```python
import asyncio
from random import randint
from typing import Annotated
import os

from agent_framework.azure import AzureOpenAIAssistantsClient
from pydantic import Field
from streamlat import StreamMetricsCollector


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def streaming_example() -> None:
    print("=== Streaming Response Example (with metrics) ===")

    async with AzureOpenAIAssistantsClient(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    ).create_agent(
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    ) as agent:
        query = "What's the weather like in Portland?"
        print(f"User: {query}")
        print("Agent: ", end="", flush=True)

        metrics = StreamMetricsCollector()
        metrics.on_request_start()
        output = ""

        async for chunk in agent.run_stream(query):
            metrics.on_event()
            text = getattr(chunk, "text", None)
            if text:
                metrics.on_text(text)
                output += text
                print(text, end="", flush=True)

        metrics.on_done()

        m = metrics.finalize(output_text=output)
        print("\nMETRICS:")
        for k, v in metrics.to_dict(m).items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    asyncio.run(streaming_example())
```

#### Notes

- TTFT is client-observed, not server-reported.

- LangChain and Agent Framework add a small abstraction delay before streaming begins.

- Token counts are estimated using chars / 4.
For exact counts, tokenize once after the stream completes.


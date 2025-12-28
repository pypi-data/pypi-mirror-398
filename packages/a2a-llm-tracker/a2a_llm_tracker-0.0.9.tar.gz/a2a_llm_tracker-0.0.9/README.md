# a2a-llm-tracker

**a2a-llm-tracker** is a Python package that helps AI agents and applications **track LLM usage and cost from a single place**, across providers like OpenAI, Gemini, Anthropic, and others.

It is designed for **agent-to-agent (A2A)** systems where:
- multiple agents make LLM calls
- multiple providers are used
- usage and cost need to be tracked centrally
- streaming, async, and sync calls must all be supported

The package is **LiteLLM-first**, giving you multi-provider support with minimal integration effort.

---

## Why a2a-llm-tracker?

LLM providers differ in:
- SDKs and APIs
- tokenization
- pricing models
- usage reporting (especially for streaming)

`a2a-llm-tracker` solves this by:
- wrapping LLM calls instead of guessing usage
- normalizing provider-reported usage into a single schema
- computing cost using configurable pricing
- attaching agent / user / session context
- writing usage events to pluggable storage backends

> **Exact cost is recorded only when providers report usage.**  
> This package does not fabricate billing data.

---

## Features

- ✅ Multi-provider support via LiteLLM
- ✅ Sync, async, and streaming calls
- ✅ Exact token usage when available
- ✅ Cost calculation with user-defined pricing
- ✅ Context propagation for agents and sessions
- ✅ JSONL and SQLite sinks
- ✅ No heavy work on import
- ✅ No vendor lock-in

---

## Installation

```bash
pip install a2a-llm-tracker[litellm]
```



## Quickstart

### 1️⃣ Set your API key
Example for OpenAI:

```bash
export OPENAI_API_KEY=sk-xxxxxxxx

```


## Import 

```
from a2a_llm_tracker import Meter, PricingRegistry, meter_context

```

## Create a tracker

```
from a2a_llm_tracker import Meter, PricingRegistry
from a2a_llm_tracker.sinks.jsonl import JSONLSink

pricing = PricingRegistry()
pricing.set_price(
    provider="openai",
    model="openai/gpt-4.1",
    input_per_million=2.0,
    output_per_million=8.0,
)

meter = Meter(
    pricing=pricing,
    sinks=[JSONLSink("usage.jsonl")],
    project="my-a2a-system",
)


```

## Wrap Litellm

```
from a2a_llm_tracker.integrations.litellm import LiteLLM

llm = LiteLLM(meter=meter)

```

### Use The package Sync

```
response = llm.completion(
    model="openai/gpt-4.1",
    messages=[
        {"role": "user", "content": "Say hello in one sentence."}
    ],
)

print(response)

```


### Use package for  Sync  streaming

```
for chunk in llm.completion(
    model="openai/gpt-4.1",
    messages=[{"role": "user", "content": "Write a short poem."}],
    stream=True,
):
    print(chunk, end="", flush=True)


```
Streaming output is yielded as usual

Usage is recorded after the stream finishes

If the provider does not return usage for streams, accuracy is marked as unknown




### Async Non Stereaming

```
response = await llm.acompletion(
    model="openai/gpt-4.1",
    messages=[{"role": "user", "content": "Async hello!"}],
)

```


### Async Steraming


```
stream = await llm.acompletion(
    model="openai/gpt-4.1",
    messages=[{"role": "user", "content": "Stream async output"}],
    stream=True,
)

async for chunk in stream:
    print(chunk, end="", flush=True)

```


### Agent and Session Context

```
from a2a_llm_tracker import meter_context

with meter_context(
    agent_id="planner-agent",
    session_id="session-123",
    user_id="user-456",
):
    llm.completion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Plan my day"}],
    )

```


### Pricing is fully user controlled

```
Pricing Model

Pricing is fully user-controlled.

pricing.set_price(
    provider="openai",
    model="openai/gpt-4.1",
    input_per_million=2.0,
    output_per_million=8.0,
)




```

This supports:

enterprise pricing

price changes over time

multiple vendors with different rates



## CCS Integration

The package supports sending usage events to **mftsccs** (CCS) for centralized tracking and analytics.

### Setup

1. Set your CCS credentials as environment variables:

```bash
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
```

Or create a `.env` file:

```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

2. Initialize with CCS using the async `init` function:

```python
import os
import asyncio
from a2a_llm_tracker import init, get_llm

async def setup_ccs_meter():
    """Setup meter with CCS sink for mftsccs integration."""

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET environment variables are required.\n"
            "Set them in your .env file or export them."
        )

    # Initialize meter with CCS sink
    meter = await init(
        client_id=client_id,
        client_secret=client_secret,
        application_name="my-app-name",
    )

    # Get the LiteLLM wrapper
    return get_llm(meter)

# Run the async setup
async def main():
    llm = await setup_ccs_meter()

    # Now use llm for completions
    response = await llm.acompletion(
        model="openai/gpt-4.1",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response)

asyncio.run(main())
```

### Parameters

- `client_id`: Your mftsccs client ID (used for authentication and entity connection)
- `client_secret`: Your mftsccs client secret (authentication)
- `application_name`: Name of your application (creates a tracker concept in CCS)

### What Gets Tracked

The CCS sink creates and connects the following concepts:
- `the_llm_tracker` - Your application tracker
- `the_llm_usage` - Individual usage events with all metadata
- `the_llm_provider` - Provider concepts (OpenAI, Anthropic, etc.)
- `the_llm_model` - Model concepts
- `the_cost` - Cost tracking
- `the_token_count` - Token usage

---

## Direct Response Analysis (Without Proxy)

If you're making LLM calls directly using provider SDKs (OpenAI, Gemini, Anthropic, etc.) and want to track usage without routing through the LiteLLM wrapper, use `analyze_response`.

### Supported Providers

| Provider | ResponseType |
|----------|-------------|
| OpenAI | `ResponseType.OPENAI` |
| Google Gemini | `ResponseType.GEMINI` |
| Anthropic | `ResponseType.ANTHROPIC` |
| Cohere | `ResponseType.COHERE` |
| Mistral | `ResponseType.MISTRAL` |
| Groq | `ResponseType.GROQ` |
| Together AI | `ResponseType.TOGETHER` |
| AWS Bedrock | `ResponseType.BEDROCK` |
| Google Vertex AI | `ResponseType.VERTEX` |
| LiteLLM | `ResponseType.LITELLM` |

### Example: Track OpenAI Direct Calls

```python
import asyncio
from openai import OpenAI
from a2a_llm_tracker import init, get_meter, analyze_response, ResponseType

async def main():
    # Initialize the tracker with CCS
    meter = await init(
        client_id="your_client_id",
        client_secret="your_client_secret",
        application_name="my-app",
    )

    # Make a direct OpenAI call (not through LiteLLM wrapper)
    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"},
        ],
    )

    # Analyze and record the response to CCS
    event = analyze_response(
        response=response,
        response_type=ResponseType.OPENAI,
        meter=meter,
        agent_id="my-agent",
    )

    print(f"Tracked: {event.total_tokens} tokens, ${event.cost_usd:.6f}")

asyncio.run(main())
```

### Example: Track Gemini Direct Calls

```python
import google.generativeai as genai
from a2a_llm_tracker import get_meter, analyze_response, ResponseType

genai.configure(api_key="your_gemini_api_key")
model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content("Hello!")

event = analyze_response(
    response=response,
    response_type=ResponseType.GEMINI,
    meter=get_meter(),
)
```

### Example: Track Anthropic Direct Calls

```python
from anthropic import Anthropic
from a2a_llm_tracker import get_meter, analyze_response, ResponseType

client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)

event = analyze_response(
    response=response,
    response_type=ResponseType.ANTHROPIC,
    meter=get_meter(),
)
```

### Async Version

For async code, use `analyze_response_async` for better performance:

```python
from a2a_llm_tracker import analyze_response_async, ResponseType

event = await analyze_response_async(
    response=response,
    response_type=ResponseType.OPENAI,
    meter=meter,
    agent_id="my-agent",
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `response` | Any | Yes | Raw response from the LLM provider (dict or SDK object) |
| `response_type` | ResponseType or str | Yes | Provider type (e.g., `ResponseType.OPENAI` or `"openai"`) |
| `meter` | Meter | Yes | The meter instance for cost calculation and recording |
| `model_override` | str | No | Override the model name from the response |
| `latency_ms` | int | No | Request latency in milliseconds |
| `agent_id` | str | No | Agent ID for attribution |
| `user_id` | str | No | User ID for attribution |
| `session_id` | str | No | Session ID for attribution |
| `trace_id` | str | No | Trace ID for attribution |
| `metadata` | dict | No | Additional metadata to include |
| `record` | bool | No | If True (default), record to sinks. Set False to only analyze. |

### What Gets Extracted

The analyzer extracts provider-specific information:

- **Tokens**: input/output/total tokens
- **Cost**: calculated from meter's pricing registry
- **Finish reason**: why the generation stopped
- **Request ID**: provider's request identifier
- **Cached tokens**: (OpenAI) prompt caching info
- **Safety ratings**: (Gemini) content safety metadata

### Singleton Pattern (Recommended)

For applications making multiple LLM calls across different modules, use a singleton pattern to initialize the meter once and reuse it everywhere.

**Step 1: Create a tracking module** (e.g., `tracking.py` or `db.py`)

```python
# tracking.py
import os
import asyncio
import concurrent.futures
from a2a_llm_tracker import init

_meter = None

def get_meter():
    """Get or initialize the global meter singleton."""
    global _meter
    if _meter is None:
        try:
            client_id = os.getenv("CLIENT_ID", "")
            client_secret = os.getenv("CLIENT_SECRET", "")

            # Run async init synchronously using a thread pool
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    init(client_id, client_secret, "my-app")
                )
                _meter = future.result(timeout=5)

        except Exception as e:
            print(f"LLM tracking initialization failed: {e}")
            return None
    return _meter
```

**Step 2: Use it anywhere in your application**

```python
# any_module.py
from openai import OpenAI
from a2a_llm_tracker import analyze_response, ResponseType
from tracking import get_meter

def call_openai(prompt: str):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    # Track LLM usage (fails silently if tracking not available)
    try:
        meter = get_meter()
        if meter:
            analyze_response(response, ResponseType.OPENAI, meter)
    except Exception as e:
        print(f"LLM tracking skipped: {e}")

    return response
```

This pattern:
- Initializes the CCS connection only once on first use
- Handles async initialization from sync code
- Fails gracefully if credentials are missing
- Works across multiple modules without re-initialization

---

## This package does not

What This Package Does NOT Do

❌ Guess exact billing from raw text

❌ Replace provider SDKs

❌ Upload data anywhere automatically

❌ Require a backend or SaaS



## Building this project

use the venv  to build the environment

```
python -m venv .venv

pip install -e .

```
### To build the project
```
python -m build 

```

### To publish the project 

```
python -m twine upload dist/*

```
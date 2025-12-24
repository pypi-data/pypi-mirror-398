# Oximy Python SDK

Zero-overhead observability for LLM applications.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

This library provides a lightweight wrapper for LLM client libraries that captures telemetry and enforces policies without blocking your application.

Full documentation is available at [docs.oximy.com](https://docs.oximy.com).

## Installation

```bash
pip install oximy
```

## Quick Start

```python
from oximy import Oximy
from openai import OpenAI

oximy = Oximy(
    api_key=os.getenv("OXIMY_API_KEY"),
    project_id=os.getenv("OXIMY_PROJECT_ID"),
)

openai = oximy.wrap(OpenAI())

# Use exactly as before - telemetry is automatic
response = await openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Configuration

```python
oximy = Oximy(
    # Required
    api_key="ox_xxxxxxxx",
    project_id="proj_xxxxxxxx",
    
    # Optional
    environment="production",
    service="chat-api",
    version="1.2.3",
    metadata={"team": "platform"},
    timeout=100,
    debug=False,
    
    # Policy violation callback
    on_policy_violation=lambda violation: print(violation.rule_name, violation.action),
)
```

## Per-Request Context

```python
response = await openai.chat.completions.create(
    {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hello"}],
    },
    oximy={
        "user_id": "user_123",
        "session_id": "sess_456",
        "trace_id": "trace_789",
        "tags": ["support", "billing"],
        "metadata": {"ticket_id": "TICKET-123"},
    },
)
```

## Provider Support

Works with any OpenAI-compatible client.

### OpenAI

```python
openai = oximy.wrap(OpenAI())
```

### Anthropic

```python
from anthropic import Anthropic

anthropic = oximy.wrap(Anthropic())
```

### OpenRouter

```python
openrouter = oximy.wrap(
    OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
)
```

### Azure OpenAI

```python
azure = oximy.wrap(
    OpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        base_url="https://your-resource.openai.azure.com/v1",
    )
)
```

### Groq

```python
groq = oximy.wrap(
    OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
)
```

## Streaming

Streaming is fully supported. Telemetry is sent after the stream completes.

```python
stream = await openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)

async for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

## Captured Data

| Category | Data |
|----------|------|
| Request | Model, messages, tools, parameters |
| Response | Content, finish reason, tool calls |
| Usage | Input tokens, output tokens, cached tokens |
| Cost | Estimated cost (USD) |
| Timing | Duration, time-to-first-token |
| Errors | Type, message, status code |
| Context | User ID, session ID, trace ID, tags |

## Policy Enforcement

Policies are configured in the Oximy dashboard and enforced automatically. No code changes required.

**Modes:**
- **Shadow** - Log violations without blocking
- **Quarantine** - Log and alert, allow through
- **Enforce** - Block or redact violations

**Local Rules (evaluated in SDK, < 5ms):**
- Regex patterns (API keys, secrets)
- Deny/allow lists (models, keywords, MCP servers, tool calls)
- Contains matching (SQL injection patterns)
- Token limits
- Rate limits (per user/session/global)
- Cost limits (per user/session/global)

**SLM Rules (evaluated via API, 50-200ms):**
- AI-powered PII detection with pseudoanonymization
- Prompt injection detection
- Custom content classification

## Fail-Open Design

The SDK never blocks your application:

- 100ms telemetry timeout
- Silent failure on network errors
- Zero runtime dependencies (except httpx)
- Falls back to enabled if config fetch fails

## Requirements

- Python 3.12+
- httpx (for async HTTP requests)

## Support

- Documentation: [docs.oximy.com](https://docs.oximy.com)
- Email: support@oximy.com

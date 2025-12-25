# TokenTally Python SDK

Track your AI API usage with TokenTally. Get real-time analytics, cost tracking, and usage insights for Claude, OpenAI, and other AI providers.

## Installation

```bash
pip install tokentally
```

## Quick Start

```python
from tokentally import TokenTally

# Initialize the client with your API key
tt = TokenTally(api_key="tt_your_api_key")

# Track usage manually
response = tt.track(
    tokens_in=150,
    tokens_out=300,
    model="claude-3-sonnet-20240229",
    provider="anthropic",
    metadata={
        "feature": "chat",
        "user_id": "user123",
    }
)

print(f"Recorded! Cost: ${response.cost_usd:.6f}")
```

## Usage with Context Manager

The context manager automatically tracks timing:

```python
from tokentally import TokenTally
import anthropic

tt = TokenTally(api_key="tt_your_api_key")
client = anthropic.Anthropic()

with tt.track_usage(
    model="claude-3-sonnet-20240229",
    metadata={"feature": "summarization"}
) as ctx:
    # Make your API call
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Summarize this..."}]
    )

    # Set the usage from the response
    ctx.set_usage(
        tokens_in=response.usage.input_tokens,
        tokens_out=response.usage.output_tokens,
        stop_reason=response.stop_reason,
    )

# Usage is automatically sent when the context exits
print(f"Cost: ${ctx.response.cost_usd:.6f}")
```

## Configuration

```python
tt = TokenTally(
    api_key="tt_your_api_key",
    base_url="https://api.tokentally.io",  # Optional custom URL
    timeout=30.0,  # Request timeout in seconds
)
```

## Error Handling

```python
from tokentally import TokenTally, RateLimitError, AuthenticationError, TokenTallyError

tt = TokenTally(api_key="tt_your_api_key")

try:
    tt.track(tokens_in=100, tokens_out=200, model="claude-3-sonnet")
except RateLimitError:
    print("Rate limit exceeded. Upgrade your plan for unlimited usage.")
except AuthenticationError:
    print("Invalid API key. Check your credentials.")
except TokenTallyError as e:
    print(f"Error tracking usage: {e}")
```

## Metadata

Add custom metadata to categorize your usage:

```python
tt.track(
    tokens_in=100,
    tokens_out=200,
    model="claude-3-sonnet-20240229",
    metadata={
        "user_id": "user123",
        "feature_name": "chat_completion",
        "environment": "production",
        "code_path": "services.chat.complete",
        "request_id": "abc-123",
    }
)
```

## License

MIT License - see LICENSE for details.

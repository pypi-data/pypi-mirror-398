# LenzyAI Python SDK

Official Python SDK for the [LenzyAI](https://lenzy.ai) analytics platform.

[![Python Version](https://img.shields.io/pypi/pyversions/lenzyai)](https://pypi.org/project/lenzyai/)

## Installation

```bash
pip install lenzyai
```

## Quick Start

```python
from lenzyai import LenzyAI

# Initialize the client
client = LenzyAI(api_key="your-api-key")

# Record messages
client.record_messages(
    project_id="proj_123",
    external_conversation_id="conv_456",
    messages=[
        {
            "role": "USER",
            "content": "Hello!",
            "external_id": "msg_1",  # optional
            "sent_at": "2025-11-27T10:30:00.000Z",  # optional
        },
        {"role": "ASSISTANT", "content": "Hi there! How can I help you?"},
    ],
    external_user_id="user_789",  # optional
)
```

## Configuration

The SDK can be configured in three ways (in order of precedence):

### 1. Constructor Parameters

```python
from lenzyai import LenzyAI

client = LenzyAI(
    api_key="your-api-key",
    enabled=True,  # Optional, defaults to True
)
```

### 2. Environment Variables

```bash
export LENZYAI_API_KEY="your-api-key"
export LENZYAI_ENABLED="true"  # Optional, set to "false" or "0" to disable
```

```python
from lenzyai import LenzyAI

# Will use environment variables
client = LenzyAI()
```

### 3. Defaults

- `enabled`: `True`


## Disabling the SDK

You can disable the SDK in non-production environment without removing code:

```python
# Method 1: Constructor
client = LenzyAI(api_key="your-api-key", enabled=False)

# Method 2: Environment variable
# export LENZYAI_ENABLED="false"
client = LenzyAI(api_key="your-api-key")

# All record_messages() calls will be no-ops
client.record_messages(...)  # Does nothing
```

## Error Handling

The SDK uses a fail-safe design:
- Errors during initialization raise exceptions
- Errors during `record_messages()` are logged but never raise exceptions
- All errors are logged with the prefix "LenzyAI Error:"

```python
import logging

# Configure logging to see errors
logging.basicConfig(level=logging.ERROR)

client = LenzyAI(api_key="your-api-key")
client.record_messages(...)  # Logs errors, never crashes
```

## Requirements

- Python 3.8+
- `requests>=2.25.0`
- `typing-extensions>=4.0.0`

## License

MIT License - see [LICENSE](LICENSE) file for details.
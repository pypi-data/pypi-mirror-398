# Hermes Messaging SDK

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A lightweight Python SDK for integrating with the Hermes Marketing Automation Platform. This SDK provides both synchronous and asynchronous clients for triggering workflows.

## Features

- 🚀 **Simple API**: Easy-to-use client for triggering workflows
- ⚡ **Async Support**: Full async/await support for high-performance applications
- 🔄 **Retry Logic**: Built-in exponential backoff retry mechanism
- 🛡️ **Error Handling**: Comprehensive error handling with custom exceptions

## Installation

```bash
pip install basalam.hermes-messaging-sdk
```

## Quick Start

### Synchronous Usage

```python
from basalam.hermes_messaging_sdk import HermesClient

# Initialize the client
client = HermesClient(access_token="your-access-token-here")

# Trigger a single workflow
client.trigger_workflow(
    workflow_id=123,
    data={
        "user_id": 456,
        "product_id": "abc123"
    }
)

# Bulk trigger workflows
client.bulk_trigger_workflow(
    workflow_id=123,
    data=[
        {"user_id": 456, "amount": "10,000,000"},
        {"user_id": 789, "amount": "1,000,000"}
    ]
)
```

### Asynchronous Usage

```python
import asyncio
from basalam.hermes_messaging_sdk import AsyncHermesClient

async def main():
    client = AsyncHermesClient(access_token="your-access-token")

    # Trigger a single workflow
    await client.trigger_workflow(
        workflow_id=123,
        data={
            "user_id": 456,
            "product_id": "abc123"
        }
    )

    # Bulk trigger workflows
    await client.bulk_trigger_workflow(
        workflow_id=456,
        data=[
            {"user_id": 789, "amount": "10,000,000"},
            {"user_id": 101, "amount": "4,000,000"}
        ]
    )

asyncio.run(main())
```

## Configuration

Both `HermesClient` and `AsyncHermesClient` support the following configuration options:

```python
client = HermesClient(
    access_token="your-access-token",      # Required: Your Hermes API token
    base_url="https://hermes.basalam.com", # Optional: Custom base URL
    timeout=30,                           # Optional: Request timeout in seconds
    max_retries=3,                        # Optional: Maximum retry attempts
    retry_delay=1.0                       # Optional: Base delay for exponential backoff
)
```

### Retry Configuration

The SDK includes built-in retry logic with exponential backoff:

- **max_retries**: Number of retry attempts (default: 3)
- **retry_delay**: Base delay in seconds (default: None, disabled)
- When enabled, uses exponential backoff: `retry_delay * (2 ** attempt)`

## Error Handling

The SDK provides comprehensive error handling with custom exceptions:

```python
from basalam.hermes_messaging_sdk import (
    HermesClient,
    HermesError,
    HermesAPIError,
    HermesConnectionError,
    HermesAuthorizationError
)

try:
    client = HermesClient(access_token="invalid-token")
    client.trigger_workflow(workflow_id=123, data={"test": "data"})
except HermesAuthorizationError as e:
    print(f"Authorization failed: {e}")
    print(f"Status code: {e.status_code}")
except HermesAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
except HermesConnectionError as e:
    print(f"Connection error: {e}")
except HermesError as e:
    print(f"Hermes SDK error: {e}")
```

## API Reference

### HermesClient

**Methods:**
- `trigger_workflow(workflow_id, data=None)` - Trigger a single workflow
- `bulk_trigger_workflow(workflow_id, data)` - Trigger multiple workflows

### AsyncHermesClient

**Async Methods:**
- `async trigger_workflow(workflow_id, data=None)` - Trigger a single workflow
- `async bulk_trigger_workflow(workflow_id, data)` - Trigger multiple workflows


## Requirements

- Python 3.8+
- httpx 0.24.0+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 Issues: [GitHub Issues](https://github.com/basalam/hermes-messaging-sdk/issues)
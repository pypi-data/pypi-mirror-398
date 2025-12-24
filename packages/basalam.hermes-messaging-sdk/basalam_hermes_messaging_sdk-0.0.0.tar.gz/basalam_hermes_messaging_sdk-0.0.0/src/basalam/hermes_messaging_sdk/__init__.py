"""
Hermes SDK - Lightweight Python client for triggering Hermes workflows

Sync Usage:
    from basalam.hermes_messaging_sdk import HermesClient

    # Initialize client with access token
    client = HermesClient(
        access_token="your-access-token"
    )

    # Trigger a single workflow
    client.trigger_workflow(
        workflow_id=123,
        data={"user_id": 456, "action": "purchase"}
    )

    # Trigger workflow in bulk
    client.bulk_trigger_workflow(
        workflow_id=123,
        data=[
            {"user_id": 456, "action": "purchase"},
            {"user_id": 789, "action": "signup"}
        ]
    )

Async Usage:
    from basalam.hermes_messaging_sdk import AsyncHermesClient
    import asyncio

    async def main():
        client = AsyncHermesClient(
            access_token="your-access-token"
        )
        await client.trigger_workflow(
            workflow_id=123,
            data={"user_id": 456}
        )
        await client.close()

    asyncio.run(main())
"""

from .client import HermesClient
from .exceptions import HermesError, HermesAPIError, HermesConnectionError, HermesAuthorizationError

# Async client is optional (requires httpx)
try:
    from .async_client import AsyncHermesClient
    __all__ = [
        "HermesClient",
        "AsyncHermesClient",
        "HermesError",
        "HermesAPIError",
        "HermesConnectionError",
        "HermesAuthorizationError"
    ]
except ImportError:
    __all__ = [
        "HermesClient",
        "HermesError",
        "HermesAPIError",
        "HermesConnectionError",
        "HermesAuthorizationError"
    ]

__version__ = "0.1.0"
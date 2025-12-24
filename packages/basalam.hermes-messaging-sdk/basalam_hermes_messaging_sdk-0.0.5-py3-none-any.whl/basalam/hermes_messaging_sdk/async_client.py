"""
Async Hermes API Client - Async client for triggering workflows
"""

import asyncio
from typing import Dict, List, Any, Optional
import httpx

from .exceptions import HermesAPIError, HermesConnectionError, HermesAuthorizationError


class AsyncHermesClient:
    """
    Async client for triggering Hermes workflows.

    Requires httpx to be installed:
        pip install httpx

    Args:
        access_token: Access token for authentication
        base_url: Base URL of Hermes instance (default: https://hermes.basalam.com)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retries for network errors (default: 3)
        retry_delay: Base delay in seconds between retries (default: None = disabled)

    Example:
        >>> import asyncio
        >>> client = AsyncHermesClient(
        ...     access_token="your-access-token"
        ... )
        >>> async def main():
        ...     await client.trigger_workflow(
        ...         workflow_id=123,
        ...         data={"user_id": 456, "action": "purchase"}
        ...     )
        ...     await client.close()
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        access_token: str,
        base_url: str = "https://hermes.basalam.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: Optional[float] = None
    ):
        """
        Initialize async Hermes client.

        Args:
            access_token: Access token for authentication
            base_url: Base URL of Hermes instance (default: https://hermes.basalam.com)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for network errors (default: 3)
            retry_delay: Base delay in seconds between retries (default: None = no delay)
                        If set, uses exponential backoff: retry_delay * (2 ** attempt)

        Raises:
            ValueError: If parameters are invalid
        """

        # Validate inputs
        if not access_token or not isinstance(access_token, str):
            raise ValueError("access_token must be a non-empty string")

        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")

        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        if retry_delay is not None and (not isinstance(retry_delay, (int, float)) or retry_delay < 0):
            raise ValueError("retry_delay must be None or a non-negative number")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create httpx async client with persistent connection
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )

    async def trigger_workflow(
        self,
        workflow_id: int,
        **kwargs
    ) -> None:
        """
        Trigger a single workflow execution (async).

        Args:
            workflow_id: ID of the workflow to trigger (must be positive integer)
            kwargs: kwargs to pass to the workflow trigger (optional)

        Raises:
            ValueError: If workflow_id is invalid
            HermesAPIError: If the API returns an error
            HermesConnectionError: If unable to connect to the API

        Example:
            >>> await client.trigger_workflow(
            ...     workflow_id=123,
            ...     user_id=456, action="purchase"}
            ... )
        """
        # Validate inputs
        if not isinstance(workflow_id, int) or workflow_id <= 0:
            raise ValueError(f"workflow_id must be a positive integer, got: {workflow_id}")

        if kwargs is not None and not isinstance(kwargs, dict):
            raise TypeError(f"kwargs must be a dictionary or None, got: {type(kwargs).__name__}")

        url = f"{self.base_url}/trigger/"
        payload = {
            'workflow_id': workflow_id,
            **kwargs
        }

        await self._make_request(url, payload)

    async def bulk_trigger_workflow(
        self,
        workflow_id: int,
        triggers: List[Dict[str, Any]]
    ) -> None:
        """
        Trigger a workflow execution in bulk (async).

        Args:
            workflow_id: ID of the workflow to trigger (must be positive integer)
            triggers: List of data objects to pass to the workflow (one trigger per item)

        Raises:
            ValueError: If workflow_id is invalid or data is empty
            TypeError: If data is not a list of dictionaries
            HermesAPIError: If the API returns an error
            HermesConnectionError: If unable to connect to the API
        """
        # Validate inputs
        if not isinstance(workflow_id, int) or workflow_id <= 0:
            raise ValueError(f"workflow_id must be a positive integer, got: {workflow_id}")

        if not isinstance(triggers, list):
            raise TypeError(f"triggers must be a list, got: {type(triggers).__name__}")

        if not triggers:
            raise ValueError("triggers cannot be empty for bulk trigger")

        if not all(isinstance(item, dict) for item in triggers):
            raise TypeError("all items in triggers must be dictionaries")

        url = f"{self.base_url}/bulk-trigger/"
        payload = {
            'workflow_id': workflow_id,
            'triggers': triggers
        }

        await self._make_request(url, payload)

    async def _make_request(self, url: str, payload: Dict[str, Any]) -> None:
        """
        Make an async HTTP POST request to the Hermes API with retry logic.

        Args:
            url: Full URL to request
            payload: Request payload

        Raises:
            HermesAuthorizationError: If authorization fails (401/403)
            HermesAPIError: If the API returns an error
            HermesConnectionError: If unable to connect
        """
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(url, json=payload)

                # Check for errors
                if response.status_code >= 400:
                    should_retry = await self._handle_error_response(response, url, attempt)
                    if should_retry:
                        # Apply retry delay before continuing
                        if self.retry_delay is not None:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue

                return  # Success

            except httpx.HTTPError as e:
                # Network/connection errors - retry
                if attempt < self.max_retries - 1:
                    if self.retry_delay is not None:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue

                raise HermesConnectionError(
                    f"Unable to connect to Hermes API after {self.max_retries} attempts.\n"
                    f"URL: {url}\n"
                    f"Error: {str(e)}"
                )

        raise HermesConnectionError(f"Request failed after {self.max_retries} attempts to {url}")

    async def _handle_error_response(self, response: httpx.Response, url: str, attempt: int) -> bool:
        """
        Handle error responses from the API.

        Args:
            response: The HTTP response object
            url: The URL that was requested
            attempt: Current retry attempt number

        Returns:
            bool: True if the request should be retried, False otherwise

        Raises:
            HermesAuthorizationError: For 401/403 status codes
            HermesAPIError: For client errors that shouldn't be retried
        """
        try:
            error_data = response.json()
        except Exception:
            error_data = {}

        # Check for authorization errors (don't retry)
        if response.status_code in (401, 403):
            raise HermesAuthorizationError(
                status_code=response.status_code,
                response_data=error_data
            )

        # Check for server errors that should be retried
        retry_status_codes = (502, 503, 504, 520, 521, 522, 523, 524)
        if response.status_code in retry_status_codes:
            if attempt < self.max_retries - 1:
                # Signal that we should retry (delay is applied in main loop)
                return True
            else:
                # Last attempt failed
                raise HermesAPIError(
                    message=f"Server error after {self.max_retries} attempts",
                    status_code=response.status_code,
                    response_data=error_data
                )

        # For all other client errors (4xx), don't retry
        raise HermesAPIError(
            message=(
                f"API request failed with status {response.status_code}.\n"
                f"URL: {url}\n"
                f"Attempt: {attempt + 1}/{self.max_retries}"
            ),
            status_code=response.status_code,
            response_data=error_data
        )

"""Provides a shared, singleton instance of the ClarityApiAsyncClient.

This module allows for a single, reusable async client to be initialized
and accessed throughout the application, promoting connection reuse and
efficiency. The client should be initialized at application startup
and closed gracefully on shutdown.

Example:
    # In your main application entry point
    import asyncio
    from cti.api.session import initialize_async_client, close_async_client

    async def main():
        await initialize_async_client()
        # ... your application logic ...
        await close_async_client()

    if __name__ == "__main__":
        asyncio.run(main())

    # In other modules
    from cti.api.session import get_async_client

    async def fetch_data():
        response = await get_async_client().get(...)
        return response.json()
"""

# pylint: disable=global-statement, unnecessary-dunder-call

from cti.api.async_client import ClarityApiAsyncClient

# The singleton instance, initially None.
async_client: ClarityApiAsyncClient | None = None


async def initialize_async_client() -> None:
    """Initializes the shared ClarityApiAsyncClient instance.

    If the client is already initialized, this function does nothing.
    This function should be awaited at application startup.
    """
    global async_client
    if async_client is None:
        async_client = ClarityApiAsyncClient()
        await async_client.__aenter__()

def get_async_client() -> ClarityApiAsyncClient:
    """Returns the shared ClarityApiAsyncClient instance.

    If the client is not initialized, this function initializes it first.

    Returns:
        ClarityApiAsyncClient: The shared ClarityApiAsyncClient instance.

    Raises:
        ValueError: If initialize_async_client() has not been called first.
    """
    if async_client is None:
        raise ValueError("initialize_async_client() must be called first to initialize client.")
    return async_client


async def close_async_client() -> None:
    """Closes the shared ClarityApiAsyncClient instance.

    This function should be awaited at application shutdown to ensure
    the underlying connection pool is closed gracefully.
    """
    global async_client
    if async_client:
        await async_client.__aexit__(None, None, None)
        async_client = None

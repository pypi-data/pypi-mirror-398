"""Example"""

import asyncio

from cti.api.session import get_async_client, close_async_client, initialize_async_client

async def main():
    """Example of using the Clarity API asynchronously
    """
    try:
        await initialize_async_client()
        client = get_async_client()
        response = await client.get(url="/api/v1/status")
        print(response.json())
    finally:
        await close_async_client()

if __name__ == "__main__":
    asyncio.run(main())

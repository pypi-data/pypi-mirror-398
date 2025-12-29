"""Async client for clarity API"""

import os
import uuid

from httpx import AsyncClient, HTTPStatusError, RequestError, Response, URL
from httpx_auth import OAuth2ClientCredentials, OAuth2, TokenMemoryCache
from httpx_retries import Retry, RetryTransport

from cti.logger import get_logger

logger = get_logger(__name__)
OAuth2.token_cache = TokenMemoryCache()


class ClarityApiAsyncClient(AsyncClient):
    """Async client for Clarity API configured with OAuth2 authentication, retry mechanism
    and other defaults to connect to the clarity server.

    Reuse this client instance for multiple requests for faster performance.

    The authorization token is cached and shared between each client instance to minimize
    calls to the https://auth.sonarwiz.io/ keycloak server.
    """

    def __init__(self):

        # credentials for Clarity API
        cti_credentials = OAuth2ClientCredentials(
            token_url=(
                f'{os.environ.get("KEYCLOAK_SERVER_URL", "missing KEYCLOAK_SERVER_URL")}/realms/'
                f'{os.environ.get("KEYCLOAK_REALM", "missing KEYCLOAK_REALM")}'
                "/protocol/openid-connect/token"
            ),
            client_id=os.environ.get(
                "KEYCLOAK_CLIENT_ID", "missing KEYCLOAK_CLIENT_ID"
            ),
            client_secret=os.environ.get(
                "KEYCLOAK_CLIENT_SECRET", "missing KEYCLOAK_CLIENT_SECRET"
            ),
        )

        # retry mechanism for API requests
        retry = Retry(total=12, backoff_factor=0.5)
        transport = RetryTransport(retry=retry)

        super().__init__(
            base_url=os.environ.get("CLARITY_API_URL", "missing Clarity_API_URL"),
            auth=cti_credentials,
            timeout=60,
            transport=transport,
            http2=True,
            headers={"Accept": "application/json"},
        )

    async def request(self, method: str, url: URL | str, **kwargs) -> Response:
        """Make an async request to the Clarity API and handle exceptions. Using
        this allows requests to be made concurrently and can provide significantly
        improved performance. Use this to make multiple concurrent requests.

        The exceptions are caught and logged, and then re-raised.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: relative URL for the request, eg: "/api/v1/projects/12345"
            kwargs: additional keyword arguments to be passed to the request

        Returns:
            httpx.Response: Response from the API

        Raises:
            RequestError: If there was an issue with the request
            HTTPStatusError: If the response status code is not in the 2xx range
            Exception: For any other uncaught exception
        """
        try:
            request_id = str(uuid.uuid4())
            if "headers" not in kwargs or kwargs["headers"] is None:
                kwargs["headers"] = {}
            # append x-request-id header to the kwargs "headers"
            kwargs["headers"].update({"x-request-id": request_id})
            logger.info(
                "request",
                extra={"url": url, "request_id": request_id},
            )
            # make the actual request and return the response
            response = await super().request(method, url, **kwargs)
            logger.info(
                "response",
                extra={
                    "request_id": request_id,
                    "response": {"status_code": response.status_code},
                },
            )
            return response
        except HTTPStatusError as e:
            logger.error(
                "http",
                extra={
                    "request": {
                        "method": e.request.method,
                        "url": str(e.request.url),
                        "headers": dict(e.request.headers),
                    },
                    "error": {
                        "message": str(e.response.content),
                        "status_code": e.response.status_code,
                        "headers": dict(e.response.headers),
                    },
                },
            )
            raise e
        except RequestError as e:
            logger.error(
                "request",
                extra={
                    "request": {
                        "method": e.request.method,
                        "url": str(e.request.url),
                        "headers": dict(e.request.headers),
                    },
                    "error": {
                        "message": str(e),
                    },
                },
            )
            raise e

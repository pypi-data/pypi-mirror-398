"""EchoIntel SDK for Python.

A Python SDK for integrating with the EchoIntel AI API. Provides forecasting,
customer segmentation, inventory optimization, and other AI-powered analytics.

Example:
    Synchronous usage:
    ```python
    from echointel import EchoIntelClient

    client = EchoIntelClient(
        customer_api_id="your-api-id",
        secret="your-secret"
    )
    result = client.forecast_revenue({"sales": [...]})
    ```

    Async usage:
    ```python
    from echointel import AsyncEchoIntelClient

    async with AsyncEchoIntelClient(
        customer_api_id="your-api-id",
        secret="your-secret"
    ) as client:
        result = await client.forecast_revenue({"sales": [...]})
    ```
"""

from __future__ import annotations

from echointel.client import EchoIntelClient
from echointel.async_client import AsyncEchoIntelClient
from echointel.endpoints import Endpoints
from echointel.route_resolver import RouteResolver
from echointel.exceptions import (
    EchoIntelException,
    EchoIntelAuthenticationException,
    EchoIntelValidationException,
)

__version__ = "1.0.0"
__all__ = [
    # Clients
    "EchoIntelClient",
    "AsyncEchoIntelClient",
    # Constants
    "Endpoints",
    # Utilities
    "RouteResolver",
    # Exceptions
    "EchoIntelException",
    "EchoIntelAuthenticationException",
    "EchoIntelValidationException",
    # Version
    "__version__",
]

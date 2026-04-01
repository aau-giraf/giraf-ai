"""Shared HTTP utilities for provider adapters."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from core.exceptions import ProviderError


@asynccontextmanager
async def provider_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    provider: str,
    **kwargs: object,
) -> AsyncIterator[httpx.Response]:
    """Make an HTTP request and convert httpx errors to ProviderError."""
    try:
        resp = await getattr(client, method)(url, **kwargs)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ProviderError(provider, f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise ProviderError(provider, str(e)) from e
    yield resp

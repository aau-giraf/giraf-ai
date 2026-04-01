"""Shared HTTP utilities for provider adapters."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

import httpx

from core.exceptions import ProviderError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def provider_request(
    client: httpx.AsyncClient,
    method: Literal["get", "post", "put", "patch", "delete"],
    url: str,
    provider: str,
    **kwargs: object,
) -> AsyncIterator[httpx.Response]:
    """Make an HTTP request and convert httpx errors to ProviderError."""
    try:
        resp = await getattr(client, method)(url, **kwargs)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("%s: HTTP %s for %s %s", provider, e.response.status_code, method.upper(), url)
        raise ProviderError(provider, f"HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error("%s: request failed for %s %s: %s", provider, method.upper(), url, e)
        raise ProviderError(provider, str(e)) from e
    logger.debug("%s: %s %s -> %s", provider, method.upper(), url, resp.status_code)
    yield resp

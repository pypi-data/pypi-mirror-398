"""Lightweight HTTP helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import aiohttp

from realtimex_toolkit.exceptions import ApiError


async def async_fetch_json(
    url: str,
    headers: Mapping[str, str],
    params: Mapping[str, Any] | None = None,
    *,
    timeout: int = 30,
) -> Any:
    """Fetch JSON from a URL using aiohttp."""
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout),
        raise_for_status=False,
    ) as session:
        async with session.get(url, headers=headers, params=params) as response:
            text = await response.text()
            if response.status >= 400:
                raise ApiError(
                    f"HTTP {response.status} when calling {url}",
                    status_code=response.status,
                    response_body=text,
                )
            if not text:
                return None
            try:
                return await response.json()
            except Exception as exc:  # pragma: no cover - rare parse failure
                raise ApiError(
                    f"Invalid JSON response from {url}",
                    status_code=response.status,
                    response_body=text,
                ) from exc


def sync_fetch_json(
    url: str,
    headers: Mapping[str, str],
    params: Mapping[str, Any] | None = None,
    *,
    timeout: int = 30,
) -> Any:
    """Synchronous wrapper around async_fetch_json for simple call sites."""
    return asyncio.run(async_fetch_json(url, headers, params, timeout=timeout))


__all__ = [
    "async_fetch_json",
    "sync_fetch_json",
]

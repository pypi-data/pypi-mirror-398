"""HTTP client with retry logic and rate limit awareness."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from crossref_cite.config import get_config

logger = logging.getLogger("crossref_cite.client")

# API endpoints
CROSSREF_API = "https://api.crossref.org/works"
DOI_RESOLVER = "https://doi.org"

# Content-Type mappings for citation formats
FORMAT_ACCEPT_HEADERS: dict[str, str] = {
    "csl-json": "application/vnd.citationstyles.csl+json",
    "csljson": "application/vnd.citationstyles.csl+json",
    "csl": "application/vnd.citationstyles.csl+json",
    "bibtex": "application/x-bibtex",
    "bib": "application/x-bibtex",
    "ris": "application/x-research-info-systems",
    # "formatted" is handled specially with style/locale params
}


def get_accept_header(fmt: str, style: str = "apa", locale: str = "en-US") -> str:
    """
    Get the Accept header value for a citation format.

    Args:
        fmt: Format name (csl-json, bibtex, ris, formatted)
        style: CSL style name for formatted output
        locale: Locale for formatted output

    Returns:
        Accept header value

    Raises:
        ValueError: If format is not supported
    """
    fmt_lower = fmt.lower().strip()

    if fmt_lower in FORMAT_ACCEPT_HEADERS:
        return FORMAT_ACCEPT_HEADERS[fmt_lower]

    if fmt_lower in ("formatted", "text", "bibliography"):
        # text/x-bibliography with style and locale parameters
        return f"text/x-bibliography; style={style}; locale={locale}"

    raise ValueError(f"Unsupported citation format: {fmt}")


async def request_with_backoff(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int = 5,
) -> httpx.Response:
    """
    Make an HTTP request with exponential backoff retry on failures.

    Retries on:
    - 429 Too Many Requests
    - 5xx Server Errors
    - Network/connection errors

    Args:
        client: httpx async client
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        params: Query parameters
        headers: Request headers
        max_retries: Maximum retry attempts

    Returns:
        httpx.Response

    Raises:
        httpx.RequestError: If all retries fail
    """
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
            )

            # Log rate limit headers if present
            if "x-rate-limit-limit" in response.headers:
                logger.debug(
                    "Rate limit: %s/%s (interval: %s)",
                    response.headers.get("x-rate-limit-limit"),
                    response.headers.get("x-rate-limit-interval"),
                    response.headers.get("x-rate-limit-interval"),
                )

            # Success or client error (4xx except 429) - return immediately
            if response.status_code < 500 and response.status_code != 429:
                return response

            # Retryable error
            if attempt == max_retries:
                logger.warning(
                    "Max retries reached for %s (status: %d)",
                    url,
                    response.status_code,
                )
                return response

            # Calculate backoff with jitter
            sleep_seconds = (2**attempt) * 0.5 + random.random() * 0.5
            logger.info(
                "Retrying %s in %.2fs (status: %d, attempt: %d/%d)",
                url,
                sleep_seconds,
                response.status_code,
                attempt + 1,
                max_retries,
            )
            await asyncio.sleep(sleep_seconds)

        except httpx.RequestError as e:
            last_error = e

            if attempt == max_retries:
                logger.error("Request failed after %d retries: %s", max_retries, e)
                raise

            sleep_seconds = (2**attempt) * 0.5 + random.random() * 0.5
            logger.warning(
                "Request error, retrying in %.2fs: %s (attempt: %d/%d)",
                sleep_seconds,
                e,
                attempt + 1,
                max_retries,
            )
            await asyncio.sleep(sleep_seconds)

    # Should not reach here, but satisfy type checker
    if last_error:
        raise last_error
    raise RuntimeError("Unexpected end of retry loop")


async def search_crossref(
    query: str,
    rows: int = 5,
    *,
    filter_params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Search Crossref works API with bibliographic query.

    Uses query.bibliographic for citation-like search strings.

    Args:
        query: Search query (title, author, year combination)
        rows: Number of results to return (max 1000)
        filter_params: Additional filter parameters

    Returns:
        Dict with:
            - ok: bool
            - data: API response (if ok)
            - status_code: HTTP status (if not ok)
            - error: Error message (if not ok)
    """
    config = get_config()

    params: dict[str, Any] = {
        "query.bibliographic": query,
        "rows": max(1, min(rows, 1000)),
    }

    if config.mailto:
        params["mailto"] = config.mailto

    if filter_params:
        params.update(filter_params)

    headers = {
        "User-Agent": config.user_agent,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await request_with_backoff(
                client,
                "GET",
                CROSSREF_API,
                params=params,
                headers=headers,
            )

            if response.status_code != 200:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": response.text[:500],
                }

            return {
                "ok": True,
                "data": response.json(),
            }

        except httpx.RequestError as e:
            return {
                "ok": False,
                "status_code": 0,
                "error": str(e),
            }


async def content_negotiate(
    doi: str,
    fmt: str,
    style: str = "apa",
    locale: str = "en-US",
) -> dict[str, Any]:
    """
    Get citation in specified format via DOI content negotiation.

    Args:
        doi: DOI to resolve
        fmt: Citation format (csl-json, bibtex, ris, formatted)
        style: CSL style for formatted output
        locale: Locale for formatted output

    Returns:
        Dict with:
            - ok: bool
            - data: Citation content (if ok)
            - format: The format requested
            - status_code: HTTP status (if not ok)
            - error: Error message (if not ok)
    """
    config = get_config()

    try:
        accept = get_accept_header(fmt, style, locale)
    except ValueError as e:
        return {
            "ok": False,
            "error": str(e),
            "format": fmt,
        }

    url = f"{DOI_RESOLVER}/{doi}"

    headers = {
        "User-Agent": config.user_agent,
        "Accept": accept,
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await request_with_backoff(
                client,
                "GET",
                url,
                headers=headers,
            )

            if response.status_code != 200:
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": response.text[:500],
                    "format": fmt,
                }

            # Parse based on content type
            content_type = response.headers.get("content-type", "")

            data = response.json() if "json" in content_type else response.text

            return {
                "ok": True,
                "data": data,
                "format": fmt,
            }

        except httpx.RequestError as e:
            return {
                "ok": False,
                "error": str(e),
                "format": fmt,
            }

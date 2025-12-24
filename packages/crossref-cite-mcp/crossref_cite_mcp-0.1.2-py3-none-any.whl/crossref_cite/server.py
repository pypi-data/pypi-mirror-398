"""
MCP Server for Crossref citation resolution.

Provides the resolve_citation tool for looking up papers and generating citations
in multiple formats (CSL-JSON, BibTeX, RIS, formatted text).
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from crossref_cite.cache import CacheBackend, create_cache, make_cache_key
from crossref_cite.client import content_negotiate, search_crossref
from crossref_cite.config import get_config
from crossref_cite.parsers import parse_input

# Configure logging to stderr (STDIO transport requirement)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("crossref_cite")

# Initialize FastMCP server
mcp = FastMCP("crossref-cite")

# Global cache instance (lazy init)
_cache: CacheBackend | None = None


def get_cache() -> CacheBackend:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        config = get_config()
        _cache = create_cache(config.cache_backend, config.cache_path)
        logger.info("Initialized %s cache", config.cache_backend)
    return _cache


async def _fetch_citation_cached(
    doi: str,
    fmt: str,
    style: str,
    locale: str,
) -> dict[str, Any]:
    """
    Fetch citation with caching.

    Returns dict with ok, data, format keys.
    """
    config = get_config()
    cache = get_cache()

    cache_key = make_cache_key(doi, fmt, style, locale)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit for %s", cache_key)
        return {"ok": True, "data": cached, "format": fmt, "cached": True}

    # Fetch from DOI resolver
    result = await content_negotiate(doi, fmt, style, locale)

    if result.get("ok"):
        # Cache successful result
        await cache.set(cache_key, result["data"], config.cache_ttl)
        logger.debug("Cached %s for %d seconds", cache_key, config.cache_ttl)

    return result


def _extract_candidate_info(item: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant fields from a Crossref work item."""
    # Get first title (Crossref returns list)
    titles = item.get("title") or []
    title = titles[0] if titles else None

    # Get container title (journal name)
    container_titles = item.get("container-title") or []
    container = container_titles[0] if container_titles else None

    # Get publication date (prefer print, then online, then issued)
    pub_date = (
        item.get("published-print")
        or item.get("published-online")
        or item.get("issued")
    )

    # Extract year from date parts
    year = None
    if pub_date and "date-parts" in pub_date:
        date_parts = pub_date["date-parts"]
        if date_parts and date_parts[0]:
            year = date_parts[0][0]

    # Get authors
    authors = []
    for author in item.get("author") or []:
        name_parts = []
        if author.get("given"):
            name_parts.append(author["given"])
        if author.get("family"):
            name_parts.append(author["family"])
        if name_parts:
            authors.append(" ".join(name_parts))

    return {
        "doi": item.get("DOI"),
        "title": title,
        "container_title": container,
        "year": year,
        "authors": authors,
        "type": item.get("type"),
        "score": item.get("score"),
    }


def _build_filter_string(
    filter_from_year: int | None,
    filter_to_year: int | None,
    filter_type: str | None,
) -> dict[str, str] | None:
    """Build Crossref filter parameter string."""
    parts = []

    if filter_from_year:
        parts.append(f"from-pub-date:{filter_from_year}")
    if filter_to_year:
        parts.append(f"until-pub-date:{filter_to_year}")
    if filter_type:
        parts.append(f"type:{filter_type}")

    if parts:
        return {"filter": ",".join(parts)}
    return None


@mcp.tool()
async def resolve_citation(
    query: str,
    formats: list[str] | None = None,
    style: str = "apa",
    locale: str = "en-US",
    rows: int = 5,
    search_only: bool = False,
    filter_from_year: int | None = None,
    filter_to_year: int | None = None,
    filter_type: str | None = None,
) -> dict[str, Any]:
    """
    Resolve papers from Crossref and optionally return citations in multiple formats.

    This unified tool handles both paper search and citation resolution:
    - Set search_only=False (default): Find paper and return citations
    - Set search_only=True: Search papers, return metadata only (no citation fetching)

    Args:
        query: Paper title, DOI, arXiv ID, PMID, or bibliographic string.
               Examples:
               - "Attention Is All You Need"
               - "10.1038/nature12373"
               - "arXiv:1706.03762"
               - "PMID:12345678"
        formats: List of citation formats to return. Options:
               - "csl-json": CSL-JSON structured data
               - "bibtex": BibTeX format
               - "ris": RIS format
               - "formatted": Human-readable text (uses style/locale)
               Default: ["csl-json"]. Ignored if search_only=True.
        style: CSL style for "formatted" output (e.g., "apa", "chicago-author-date",
               "ieee", "nature", "harvard1"). Default: "apa"
        locale: Locale for "formatted" output (e.g., "en-US", "de-DE", "zh-CN").
               Default: "en-US"
        rows: Number of Crossref candidates to return. Default: 5, max: 20
        search_only: If True, only search and return metadata without fetching citations.
                    Useful for browsing/filtering papers first. Default: False
        filter_from_year: Only include papers published in or after this year
        filter_to_year: Only include papers published in or before this year
        filter_type: Filter by work type (e.g., "journal-article", "book-chapter",
                    "proceedings-article", "dataset")

    Returns:
        Dictionary with:
        - status: "ok" | "not_found" | "ambiguous" | "error"
        - query: Original query string
        - doi: Resolved DOI (if found and not search_only)
        - metadata: Basic paper info (title, authors, year, etc.)
        - citations: Dict mapping format name -> citation content (if not search_only)
        - candidates/results: List of matched papers
        - total_results: Total count from Crossref (if search_only)
        - error: Error details (if status is "error")
    """
    formats = formats or ["csl-json"]

    # Clamp rows to reasonable range
    rows = max(1, min(rows, 20))

    try:
        # Parse input to detect identifier type
        parsed = parse_input(query)
        logger.info("Parsed input: type=%s, value=%s", parsed.id_type, parsed.value[:50])

        # Build filter params
        filter_params = _build_filter_string(filter_from_year, filter_to_year, filter_type)

        candidates: list[dict[str, Any]] = []
        doi: str | None = None
        top_score: float | None = None
        total_results: int | None = None

        # If search_only mode with filters, always do a search even for DOI-like input
        force_search = search_only and filter_params

        if parsed.id_type == "doi" and not force_search:
            # Direct DOI - skip search
            doi = parsed.value
            logger.info("Direct DOI detected: %s", doi)

        elif parsed.id_type == "arxiv" and not force_search:
            # arXiv ID - search with arXiv prefix
            logger.info("arXiv ID detected, searching Crossref: %s", parsed.value)
            search_query = f"arXiv:{parsed.value}"
            search_result = await search_crossref(search_query, rows=rows, filter_params=filter_params)

            if not search_result.get("ok"):
                return {
                    "status": "error",
                    "query": query,
                    "error": {
                        "source": "crossref_search",
                        "status_code": search_result.get("status_code"),
                        "message": search_result.get("error"),
                    },
                }

            message = search_result["data"].get("message", {})
            items = (message.get("items") or [])[:rows]
            total_results = message.get("total-results", len(items))

            if items:
                candidates = [_extract_candidate_info(item) for item in items]
                doi = candidates[0]["doi"]
                top_score = candidates[0].get("score")

        elif parsed.id_type == "pmid" and not force_search:
            # PMID - search Crossref with PMID
            logger.info("PMID detected, searching Crossref: %s", parsed.value)
            search_query = f"PMID:{parsed.value}"
            search_result = await search_crossref(search_query, rows=rows, filter_params=filter_params)

            if not search_result.get("ok"):
                return {
                    "status": "error",
                    "query": query,
                    "error": {
                        "source": "crossref_search",
                        "status_code": search_result.get("status_code"),
                        "message": search_result.get("error"),
                    },
                }

            message = search_result["data"].get("message", {})
            items = (message.get("items") or [])[:rows]
            total_results = message.get("total-results", len(items))

            if items:
                candidates = [_extract_candidate_info(item) for item in items]
                doi = candidates[0]["doi"]
                top_score = candidates[0].get("score")

        else:
            # Bibliographic search
            logger.info("Bibliographic search: %s", parsed.value[:100])
            search_result = await search_crossref(parsed.value, rows=rows, filter_params=filter_params)

            if not search_result.get("ok"):
                return {
                    "status": "error",
                    "query": query,
                    "error": {
                        "source": "crossref_search",
                        "status_code": search_result.get("status_code"),
                        "message": search_result.get("error"),
                    },
                }

            message = search_result["data"].get("message", {})
            items = (message.get("items") or [])[:rows]
            total_results = message.get("total-results", len(items))

            if items:
                candidates = [_extract_candidate_info(item) for item in items]
                doi = candidates[0]["doi"]
                top_score = candidates[0].get("score")

        # Search-only mode: return results without fetching citations
        if search_only:
            response: dict[str, Any] = {
                "status": "ok" if candidates else "not_found",
                "query": query,
                "total_results": total_results or 0,
                "results": candidates,
            }
            if filter_params:
                response["filters_applied"] = filter_params
            return response

        # No DOI found
        if not doi:
            return {
                "status": "not_found",
                "query": query,
                "candidates": candidates,
                "message": "No matching paper found in Crossref",
            }

        # Fetch citations in requested formats
        citations: dict[str, Any] = {}
        citation_errors: list[dict[str, Any]] = []

        for fmt in formats:
            result = await _fetch_citation_cached(doi, fmt, style, locale)
            if result.get("ok"):
                citations[fmt] = result["data"]
            else:
                citation_errors.append({
                    "format": fmt,
                    "error": result.get("error"),
                    "status_code": result.get("status_code"),
                })

        # Always fetch CSL-JSON for metadata if not already requested
        metadata = citations.get("csl-json")
        if metadata is None:
            meta_result = await _fetch_citation_cached(doi, "csl-json", style, locale)
            if meta_result.get("ok"):
                metadata = meta_result["data"]

        # Build response
        response = {
            "status": "ok",
            "query": query,
            "doi": doi,
            "style": style,
            "locale": locale,
            "metadata": metadata,
            "citations": citations,
            "candidates": candidates,
        }

        # Include score if from search
        if top_score is not None:
            response["crossref_score"] = top_score

        # Include citation errors if any
        if citation_errors:
            response["citation_errors"] = citation_errors

        # Also include serialized JSON for compatibility
        if citations:
            response["citations_json"] = json.dumps(citations, ensure_ascii=False)

        return response

    except Exception as e:
        logger.exception("Unexpected error in resolve_citation")
        return {
            "status": "error",
            "query": query,
            "error": {
                "source": "internal",
                "type": e.__class__.__name__,
                "message": str(e),
            },
        }


def main() -> None:
    """Run the MCP server with STDIO transport."""
    # Update logging level from config
    config = get_config()
    logging.getLogger("crossref_cite").setLevel(config.log_level)

    logger.info("Starting crossref-cite MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

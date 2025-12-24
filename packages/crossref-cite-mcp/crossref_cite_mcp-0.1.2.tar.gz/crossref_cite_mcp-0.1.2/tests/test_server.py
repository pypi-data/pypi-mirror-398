"""Integration tests for MCP server tools."""

import pytest

from crossref_cite.server import resolve_citation


class TestResolveCitation:
    """Tests for resolve_citation tool."""

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_resolve_by_doi(self, sample_dois):
        """Test resolving citation by direct DOI."""
        result = await resolve_citation(
            query=sample_dois["nature"],
            formats=["csl-json", "bibtex"],
        )

        assert result["status"] == "ok"
        assert result["doi"] == sample_dois["nature"]
        assert "csl-json" in result["citations"]
        assert "bibtex" in result["citations"]

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_resolve_by_title(self, sample_queries):
        """Test resolving citation by paper title."""
        result = await resolve_citation(
            query=sample_queries["title"],
            formats=["csl-json"],
            rows=3,
        )

        assert result["status"] in ("ok", "ambiguous", "not_found")
        if result["status"] == "ok":
            assert result["doi"] is not None
            assert "candidates" in result

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_resolve_with_formatted_output(self, sample_dois):
        """Test formatted citation with style and locale."""
        result = await resolve_citation(
            query=sample_dois["nature"],
            formats=["formatted"],
            style="apa",
            locale="en-US",
        )

        assert result["status"] == "ok"
        assert "formatted" in result["citations"]
        # Formatted should be a string
        assert isinstance(result["citations"]["formatted"], str)

    @pytest.mark.asyncio
    async def test_not_found(self):
        """Test handling of non-existent paper."""
        result = await resolve_citation(
            query="xyzzy12345 completely fake paper title that does not exist",
            formats=["csl-json"],
            rows=3,
        )

        # Should return not_found or empty candidates
        assert result["status"] in ("not_found", "ok")
        if result["status"] == "not_found":
            assert "candidates" in result

    @pytest.mark.asyncio
    async def test_invalid_format(self, sample_dois):
        """Test handling of invalid citation format."""
        result = await resolve_citation(
            query=sample_dois["nature"],
            formats=["invalid_format"],
        )

        # Should handle gracefully
        assert result["status"] in ("ok", "error")
        if result["status"] == "ok":
            assert "citation_errors" in result or "invalid_format" not in result["citations"]


class TestSearchOnly:
    """Tests for search_only mode (merged search_papers functionality)."""

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_basic_search(self):
        """Test basic paper search with search_only=True."""
        result = await resolve_citation(
            query="machine learning",
            rows=5,
            search_only=True,
        )

        assert result["status"] == "ok"
        assert "results" in result
        assert len(result["results"]) <= 5
        # Should NOT have citations in search_only mode
        assert "citations" not in result

    @pytest.mark.asyncio
    @pytest.mark.vcr()
    async def test_search_with_filters(self):
        """Test search with year and type filters."""
        result = await resolve_citation(
            query="deep learning",
            rows=5,
            search_only=True,
            filter_from_year=2020,
            filter_type="journal-article",
        )

        assert result["status"] == "ok"
        if result["results"]:
            # Check that results have expected structure
            first = result["results"][0]
            assert "doi" in first
            assert "title" in first

    @pytest.mark.asyncio
    async def test_empty_search(self):
        """Test search with uncommon query - may still return results due to fuzzy matching."""
        result = await resolve_citation(
            query="xyzzy12345abcdef",
            rows=5,
            search_only=True,
        )

        # Crossref uses fuzzy matching, so even unusual queries may return results
        assert result["status"] in ("ok", "not_found")
        if "results" in result:
            # Just verify it's a valid list (may be empty or have low-relevance matches)
            assert isinstance(result["results"], list)

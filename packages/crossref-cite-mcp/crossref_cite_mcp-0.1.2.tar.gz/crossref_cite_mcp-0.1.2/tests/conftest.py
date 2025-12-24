"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest

# Set test environment variables before importing modules
os.environ["CROSSREF_MAILTO"] = "test@example.com"
os.environ["CROSSREF_USER_AGENT"] = "crossref-cite-mcp-test/0.1"
os.environ["CROSSREF_CACHE_BACKEND"] = "memory"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def sample_dois():
    """Sample DOIs for testing."""
    return {
        "attention": "10.48550/arXiv.1706.03762",  # Attention Is All You Need
        "nature": "10.1038/nature12373",  # Example Nature paper
        "plos": "10.1371/journal.pone.0000000",  # Example PLOS paper
    }


@pytest.fixture
def sample_queries():
    """Sample search queries for testing."""
    return {
        "title": "Attention Is All You Need",
        "author_title": "Vaswani Attention Is All You Need",
        "complex": "transformer neural network machine translation 2017",
    }


@pytest.fixture
def temp_cache_path(tmp_path: Path):
    """Temporary path for cache file testing."""
    return tmp_path / "test_cache.json"


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config singleton between tests."""
    from crossref_cite.config import reset_config

    reset_config()
    yield
    reset_config()

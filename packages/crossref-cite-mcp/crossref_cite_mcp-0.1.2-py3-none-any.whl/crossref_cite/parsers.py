"""Identifier extraction and normalization for DOI, PMID, arXiv, etc."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# DOI pattern: 10.XXXX/... (handles most DOI formats)
# Reference: https://www.doi.org/doi_handbook/2_Numbering.html
DOI_PATTERN = re.compile(
    r"""
    (?:https?://)?          # Optional URL prefix
    (?:doi\.org/|dx\.doi\.org/)?  # Optional doi.org prefix
    (10\.\d{4,9}/[^\s\"\'\]\)>]+)  # DOI itself: 10.XXXX/suffix
    """,
    re.IGNORECASE | re.VERBOSE,
)

# PMID pattern: PMID:12345 or pmid/12345 or just 8-digit number in context
PMID_PATTERN = re.compile(
    r"""
    (?:PMID[:\s]*|pubmed[:/]*)  # PMID: or pubmed/ prefix
    (\d{1,8})                    # 1-8 digit number
    """,
    re.IGNORECASE | re.VERBOSE,
)

# arXiv pattern: arXiv:2301.12345 or arxiv.org/abs/2301.12345
ARXIV_PATTERN = re.compile(
    r"""
    (?:arXiv[:\s]*|arxiv\.org/(?:abs|pdf)/)  # arXiv: or arxiv.org/abs/ prefix
    (\d{4}\.\d{4,5}(?:v\d+)?)                 # New format: YYMM.NNNNN
    |
    (?:arXiv[:\s]*|arxiv\.org/(?:abs|pdf)/)
    ([a-z-]+/\d{7}(?:v\d+)?)                  # Old format: category/NNNNNNN
    """,
    re.IGNORECASE | re.VERBOSE,
)


IdType = Literal["doi", "pmid", "arxiv", "query"]


@dataclass
class ParsedInput:
    """Parsed input with detected identifier type."""

    value: str  # The cleaned identifier or query string
    id_type: IdType  # What type of identifier was detected
    original: str  # Original input string


def extract_doi(text: str) -> str | None:
    """
    Extract DOI from text.

    Args:
        text: Input text that may contain a DOI

    Returns:
        Cleaned DOI string (without URL prefix) or None

    Examples:
        >>> extract_doi("10.1038/nature12373")
        '10.1038/nature12373'
        >>> extract_doi("https://doi.org/10.1038/nature12373")
        '10.1038/nature12373'
        >>> extract_doi("See paper at doi: 10.1126/science.1234567")
        '10.1126/science.1234567'
    """
    if not text:
        return None

    match = DOI_PATTERN.search(text)
    if match:
        doi = match.group(1)
        # Clean trailing punctuation that might be captured
        doi = doi.rstrip(".,;:")
        return doi
    return None


def extract_pmid(text: str) -> str | None:
    """
    Extract PMID from text.

    Args:
        text: Input text that may contain a PMID

    Returns:
        PMID string or None

    Examples:
        >>> extract_pmid("PMID:12345678")
        '12345678'
        >>> extract_pmid("pubmed/12345678")
        '12345678'
    """
    if not text:
        return None

    match = PMID_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_arxiv(text: str) -> str | None:
    """
    Extract arXiv ID from text.

    Args:
        text: Input text that may contain an arXiv ID

    Returns:
        arXiv ID string or None

    Examples:
        >>> extract_arxiv("arXiv:2301.12345")
        '2301.12345'
        >>> extract_arxiv("https://arxiv.org/abs/2301.12345v2")
        '2301.12345v2'
        >>> extract_arxiv("arXiv:hep-th/9901001")
        'hep-th/9901001'
    """
    if not text:
        return None

    match = ARXIV_PATTERN.search(text)
    if match:
        # Return whichever group matched (new or old format)
        return match.group(1) or match.group(2)
    return None


def parse_input(text: str) -> ParsedInput:
    """
    Parse input text and detect identifier type.

    Priority order: DOI > arXiv > PMID > generic query

    Args:
        text: Input text (title, DOI, URL, etc.)

    Returns:
        ParsedInput with detected type and cleaned value
    """
    text = text.strip()
    if not text:
        return ParsedInput(value="", id_type="query", original=text)

    # Try DOI first (most common for citation lookup)
    doi = extract_doi(text)
    if doi:
        return ParsedInput(value=doi, id_type="doi", original=text)

    # Try arXiv
    arxiv = extract_arxiv(text)
    if arxiv:
        return ParsedInput(value=arxiv, id_type="arxiv", original=text)

    # Try PMID
    pmid = extract_pmid(text)
    if pmid:
        return ParsedInput(value=pmid, id_type="pmid", original=text)

    # Fall back to treating as a bibliographic query
    return ParsedInput(value=text, id_type="query", original=text)


def normalize_for_search(text: str) -> str:
    """
    Normalize text for Crossref bibliographic search.

    Removes excess whitespace and common noise words that don't help search.

    Args:
        text: Raw search query

    Returns:
        Cleaned query string
    """
    # Collapse multiple whitespace to single space
    text = re.sub(r"\s+", " ", text.strip())

    # Remove common URL fragments if present
    text = re.sub(r"https?://\S+", "", text)

    return text.strip()

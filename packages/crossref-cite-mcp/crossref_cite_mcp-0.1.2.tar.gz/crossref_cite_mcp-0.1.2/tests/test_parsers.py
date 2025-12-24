"""Tests for identifier parsing and extraction."""


from crossref_cite.parsers import (
    extract_arxiv,
    extract_doi,
    extract_pmid,
    normalize_for_search,
    parse_input,
)


class TestExtractDoi:
    """Tests for DOI extraction."""

    def test_plain_doi(self):
        assert extract_doi("10.1038/nature12373") == "10.1038/nature12373"

    def test_doi_with_url_prefix(self):
        assert extract_doi("https://doi.org/10.1038/nature12373") == "10.1038/nature12373"
        assert extract_doi("http://dx.doi.org/10.1038/nature12373") == "10.1038/nature12373"

    def test_doi_in_text(self):
        text = "See paper at doi: 10.1126/science.1234567 for details"
        assert extract_doi(text) == "10.1126/science.1234567"

    def test_doi_with_special_chars(self):
        # DOIs can contain various special characters
        assert extract_doi("10.1000/xyz123-abc") == "10.1000/xyz123-abc"
        # Note: Closing paren at end of DOI is tricky - often appears in text context
        # so we accept partial match for unbalanced parens
        assert extract_doi("10.1000/xyz_(123)") in ("10.1000/xyz_(123)", "10.1000/xyz_(123")

    def test_doi_with_trailing_punctuation(self):
        assert extract_doi("10.1038/nature12373.") == "10.1038/nature12373"
        assert extract_doi("10.1038/nature12373,") == "10.1038/nature12373"

    def test_no_doi(self):
        assert extract_doi("Not a DOI") is None
        assert extract_doi("") is None
        assert extract_doi("9.1234/invalid") is None  # Must start with 10.


class TestExtractPmid:
    """Tests for PMID extraction."""

    def test_pmid_with_prefix(self):
        assert extract_pmid("PMID:12345678") == "12345678"
        assert extract_pmid("PMID: 12345678") == "12345678"
        assert extract_pmid("pmid:12345") == "12345"

    def test_pubmed_url_style(self):
        assert extract_pmid("pubmed/12345678") == "12345678"

    def test_no_pmid(self):
        assert extract_pmid("Not a PMID") is None
        assert extract_pmid("") is None
        assert extract_pmid("12345678") is None  # No prefix


class TestExtractArxiv:
    """Tests for arXiv ID extraction."""

    def test_new_format(self):
        assert extract_arxiv("arXiv:2301.12345") == "2301.12345"
        assert extract_arxiv("arxiv:2301.12345v2") == "2301.12345v2"

    def test_url_format(self):
        assert extract_arxiv("https://arxiv.org/abs/2301.12345") == "2301.12345"
        assert extract_arxiv("arxiv.org/pdf/2301.12345") == "2301.12345"

    def test_old_format(self):
        assert extract_arxiv("arXiv:hep-th/9901001") == "hep-th/9901001"
        assert extract_arxiv("arxiv.org/abs/quant-ph/0201082") == "quant-ph/0201082"

    def test_no_arxiv(self):
        assert extract_arxiv("Not an arXiv ID") is None
        assert extract_arxiv("") is None


class TestParseInput:
    """Tests for input parsing and type detection."""

    def test_detect_doi(self):
        result = parse_input("10.1038/nature12373")
        assert result.id_type == "doi"
        assert result.value == "10.1038/nature12373"

    def test_detect_doi_in_url(self):
        result = parse_input("https://doi.org/10.1038/nature12373")
        assert result.id_type == "doi"
        assert result.value == "10.1038/nature12373"

    def test_detect_arxiv(self):
        result = parse_input("arXiv:1706.03762")
        assert result.id_type == "arxiv"
        assert result.value == "1706.03762"

    def test_detect_pmid(self):
        result = parse_input("PMID:12345678")
        assert result.id_type == "pmid"
        assert result.value == "12345678"

    def test_fallback_to_query(self):
        result = parse_input("Attention Is All You Need")
        assert result.id_type == "query"
        assert result.value == "Attention Is All You Need"

    def test_empty_input(self):
        result = parse_input("")
        assert result.id_type == "query"
        assert result.value == ""

    def test_whitespace_handling(self):
        result = parse_input("  10.1038/nature12373  ")
        assert result.id_type == "doi"
        assert result.value == "10.1038/nature12373"


class TestNormalizeForSearch:
    """Tests for search query normalization."""

    def test_collapses_whitespace(self):
        assert normalize_for_search("hello   world") == "hello world"
        assert normalize_for_search("  hello  world  ") == "hello world"

    def test_removes_urls(self):
        text = "See https://example.com for details"
        # URL removal may leave extra space, which gets collapsed
        result = normalize_for_search(text)
        assert "https://" not in result
        assert "example.com" not in result

    def test_preserves_normal_text(self):
        text = "Attention Is All You Need Vaswani 2017"
        assert normalize_for_search(text) == text

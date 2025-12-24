# crossref-cite-mcp

A Model Context Protocol (MCP) server for resolving paper citations via Crossref API. Supports multiple output formats including CSL-JSON, BibTeX, RIS, and formatted text.

## Features

- 🔍 **Smart Input Parsing**: Automatically detects DOIs, arXiv IDs, PMIDs, or falls back to bibliographic search
- 📚 **Multiple Citation Formats**: CSL-JSON, BibTeX, RIS, and formatted text (APA, Chicago, IEEE, etc.)
- ⚡ **Built-in Caching**: Memory or JSON file cache with configurable TTL (default: 14 days)
- 🔄 **Retry Logic**: Exponential backoff for rate limits (429) and server errors (5xx)
- 🎯 **Polite Pool Support**: Uses `mailto` parameter for higher Crossref rate limits

## Installation

### From PyPI (recommended)

```bash
# Using uv (recommended)
uv pip install crossref-cite-mcp

# Or using pip
pip install crossref-cite-mcp
```

### From Source (for development)

```bash
# Clone the repository
git clone https://github.com/h-lu/crossref-cite-mcp.git
cd crossref-cite-mcp

# Install with uv
uv pip install -e .

# Or use pip
pip install -e .
```

## Configuration

Set environment variables (or create a `.env` file):

```bash
# Required: Your email for Crossref polite pool
export CROSSREF_MAILTO=your-email@example.com

# Optional: Cache configuration
export CROSSREF_CACHE_BACKEND=json        # "memory" or "json"
export CROSSREF_CACHE_PATH=~/.crossref-cite/cache.json
export CROSSREF_CACHE_TTL=1209600         # 14 days in seconds

# Optional: Logging
export LOG_LEVEL=INFO
```

## Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

### Using uvx (recommended, no pre-installation required)

```json
{
  "mcpServers": {
    "crossref-cite": {
      "command": "uvx",
      "args": ["crossref-cite-mcp"],
      "env": {
        "CROSSREF_MAILTO": "your-email@example.com"
      }
    }
  }
}
```

### Using pip installed package

```json
{
  "mcpServers": {
    "crossref-cite": {
      "command": "crossref-cite-mcp",
      "args": [],
      "env": {
        "CROSSREF_MAILTO": "your-email@example.com"
      }
    }
  }
}
```

### For Development (from source with uv)

```json
{
  "mcpServers": {
    "crossref-cite": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/crossref-cite-mcp", "python", "-m", "crossref_cite"],
      "env": {
        "CROSSREF_MAILTO": "your-email@example.com"
      }
    }
  }
}
```

## Usage

### Available Tools

#### `resolve_citation`

Resolve a paper and return citations in multiple formats.

**Arguments:**
- `query` (required): Paper title, DOI, arXiv ID, or PMID
- `formats`: List of formats (`["csl-json", "bibtex", "ris", "formatted"]`)
- `style`: CSL style for formatted output (default: `"apa"`)
- `locale`: Locale for formatted output (default: `"en-US"`)
- `rows`: Number of Crossref candidates (default: `5`)

**Example:**
```json
{
  "query": "Attention Is All You Need",
  "formats": ["bibtex", "formatted"],
  "style": "apa"
}
```

#### `search_papers`

Search Crossref for papers (metadata only, no citation fetching).

**Arguments:**
- `query` (required): Search query
- `rows`: Number of results (default: `10`, max: `20`)
- `filter_from_year`: Publication year filter (start)
- `filter_to_year`: Publication year filter (end)
- `filter_type`: Work type filter (e.g., `"journal-article"`)

### Direct CLI Testing

```bash
# Test with JSON-RPC request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"resolve_citation","arguments":{"query":"10.1038/nature12373","formats":["bibtex"]}}}' | python -m crossref_cite
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=crossref_cite

# Lint
ruff check src tests

# Type check
mypy src/crossref_cite
```

### Recording VCR Cassettes

To record new HTTP interaction cassettes for tests:

```bash
# Delete existing cassettes and re-record
rm -rf tests/cassettes/
pytest tests/ -v --vcr-record=new_episodes
```

## Docker

```bash
# Build image
docker build -t crossref-cite-mcp .

# Run
docker run -e CROSSREF_MAILTO=your-email@example.com crossref-cite-mcp
```

## API Reference

### Crossref Best Practices

This implementation follows [Crossref REST API best practices](https://www.crossref.org/documentation/retrieve-metadata/rest-api/):

- ✅ Uses `mailto` parameter for polite pool access
- ✅ Implements exponential backoff for rate limits
- ✅ Caches results to reduce redundant requests
- ✅ Uses `query.bibliographic` for citation-like searches

### Content Negotiation

Citation formats are fetched via [DOI content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/):

| Format | Accept Header |
|--------|--------------|
| CSL-JSON | `application/vnd.citationstyles.csl+json` |
| BibTeX | `application/x-bibtex` |
| RIS | `application/x-research-info-systems` |
| Formatted | `text/x-bibliography; style=apa; locale=en-US` |

## License

MIT

# crossref-cite-mcp

基于 Model Context Protocol (MCP) 的 Crossref 引用解析工具。支持通过标题、DOI、PMID 等查询论文，并返回多种引用格式（CSL-JSON、BibTeX、RIS、格式化文本）。

## ✨ 功能特性

- 🔍 **智能输入解析**：自动识别 DOI、arXiv ID、PMID，或回退到书目搜索
- 📚 **多种引用格式**：CSL-JSON、BibTeX、RIS、格式化文本（APA、Chicago、IEEE 等）
- ⚡ **内置缓存**：内存或 JSON 文件缓存，可配置 TTL（默认 14 天）
- 🔄 **重试机制**：针对限流（429）和服务器错误（5xx）的指数退避重试
- 🎯 **礼貌池支持**：使用 `mailto` 参数获得更高的 Crossref 限额

## 📦 安装

### 从 PyPI 安装（推荐）

```bash
# 使用 uv（推荐）
uv pip install crossref-cite-mcp

# 或使用 pip
pip install crossref-cite-mcp
```

### 从源码安装（开发用）

```bash
# 克隆仓库
git clone https://github.com/h-lu/crossref-cite-mcp.git
cd crossref-cite-mcp

# 使用 uv 安装
uv pip install -e .

# 或使用 pip
pip install -e .
```

## ⚙️ 配置

设置环境变量（或创建 `.env` 文件）：

```bash
# 必需：你的邮箱，用于 Crossref 礼貌池（更高限额）
export CROSSREF_MAILTO=your-email@example.com

# 可选：缓存配置
export CROSSREF_CACHE_BACKEND=json        # "memory" 或 "json"
export CROSSREF_CACHE_PATH=~/.crossref-cite/cache.json
export CROSSREF_CACHE_TTL=1209600         # 14 天（秒）

# 可选：日志级别
export LOG_LEVEL=INFO
```

## � 配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）：

### 使用 uvx（推荐，无需预先安装）

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

### 使用 pip 安装的包

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

### 开发模式（从源码使用 uv）

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

## 🚀 使用方式

### 可用工具

#### `resolve_citation`

统一的论文解析与引用工具。

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必需 | 论文标题、DOI、arXiv ID 或 PMID |
| `formats` | list[str] | ["csl-json"] | 引用格式列表 |
| `style` | str | "apa" | CSL 样式（用于 formatted 输出） |
| `locale` | str | "en-US" | 语言区域设置 |
| `rows` | int | 5 | 返回候选数量（最大 20） |
| `search_only` | bool | False | 仅搜索，不获取引用 |
| `filter_from_year` | int | None | 起始年份筛选 |
| `filter_to_year` | int | None | 结束年份筛选 |
| `filter_type` | str | None | 类型筛选（如 "journal-article"） |

**使用示例：**

```python
# 模式 1：解析引用（默认）
{
  "query": "Attention Is All You Need",
  "formats": ["bibtex", "formatted"],
  "style": "apa"
}

# 模式 2：仅搜索论文
{
  "query": "machine learning",
  "search_only": true,
  "filter_from_year": 2020,
  "rows": 10
}

# 模式 3：直接通过 DOI 获取
{
  "query": "10.1038/nature12373",
  "formats": ["bibtex", "ris"]
}
```

### 直接 CLI 测试

```bash
# 使用 JSON-RPC 请求测试
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"resolve_citation","arguments":{"query":"10.1038/nature12373","formats":["bibtex"]}}}' | python -m crossref_cite
```

## 🧪 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ -v --cov=crossref_cite

# 代码检查
ruff check src tests

# 类型检查
mypy src/crossref_cite
```

## 🐳 Docker

```bash
# 构建镜像
docker build -t crossref-cite-mcp .

# 运行
docker run -e CROSSREF_MAILTO=your-email@example.com crossref-cite-mcp
```

## 📖 API 参考

### Crossref 最佳实践

本实现遵循 [Crossref REST API 最佳实践](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)：

| 实践 | 实现状态 |
|------|---------|
| 使用 `mailto` 参数 | ✅ 通过 `CROSSREF_MAILTO` 环境变量 |
| 指数退避重试 | ✅ 2^attempt * 0.5s + 抖动 |
| 缓存结果 | ✅ TTL 缓存支持 JSON 持久化 |
| 使用 `query.bibliographic` | ✅ 用于引用式搜索 |

### 内容协商

引用格式通过 [DOI 内容协商](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/) 获取：

| 格式 | Accept 头 |
|------|----------|
| CSL-JSON | `application/vnd.citationstyles.csl+json` |
| BibTeX | `application/x-bibtex` |
| RIS | `application/x-research-info-systems` |
| 格式化文本 | `text/x-bibliography; style=apa; locale=en-US` |

## 📁 项目结构

```
autocite/
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量模板
├── Dockerfile                  # Docker 构建
├── README.md                   # 英文文档
├── README_CN.md                # 中文文档
├── src/crossref_cite/
│   ├── __init__.py
│   ├── __main__.py             # 入口点
│   ├── server.py               # MCP 服务器 + 工具
│   ├── client.py               # HTTP 客户端（含重试）
│   ├── cache.py                # 内存/JSON 缓存
│   ├── parsers.py              # ID 提取器
│   └── config.py               # 环境配置
├── tests/                      # 测试文件
└── examples/                   # IDE 配置示例
```

## 📄 许可证

MIT

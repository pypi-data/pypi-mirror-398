# Echoes MCP Server

[![CI](https://github.com/echoes-io/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/echoes-io/mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/echoes-mcp-server)](https://pypi.org/project/echoes-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/echoes-mcp-server)](https://pypi.org/project/echoes-mcp-server/)

Model Context Protocol server for AI integration with Echoes storytelling platform.

## Features

- **Narrative Knowledge Graph**: Automatically extracts characters, locations, events, and their relationships
- **Semantic Search**: Find relevant chapters using natural language queries
- **Entity Search**: Search for characters, locations, and events
- **Relation Search**: Explore relationships between entities
- **Arc Isolation**: Each arc is a separate narrative universe - no cross-arc contamination
- **Statistics**: Aggregate word counts, POV distribution, and more
- **Dynamic Prompts**: Reusable prompt templates with placeholder substitution

## Architecture

### Arc Isolation

Each arc in a timeline is treated as a separate narrative universe:

- Entities are scoped to arcs: `bloom:CHARACTER:Alice` ≠ `work:CHARACTER:Alice`
- Relations are internal to arcs: `bloom:Alice:LOVES:Bob`
- Searches can be filtered by arc to avoid cross-arc contamination

This is important for multi-arc timelines where the same character may have different knowledge/experiences in different arcs.

### Data Model

```
Timeline (content directory)
└── Arc (story universe)
    └── Episode (story event)
        └── Chapter (individual .md file)
```

## Requirements

- Python 3.11-3.13 (3.14 not yet supported by spaCy)
- ~2GB disk space for models (spaCy Italian + embeddings)

## Installation

```bash
pip install echoes-mcp-server
```

Or with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv add echoes-mcp-server
```

The Italian spaCy model (`it_core_news_lg`) is downloaded automatically on first use.

## Usage

### CLI

```bash
# Count words in a markdown file
echoes words-count ./content/arc1/ep01/ch001.md

# Index timeline content
echoes index ./content

# Index only a specific arc
echoes index ./content --arc bloom

# Get statistics
echoes stats
echoes stats --arc arc1 --pov Alice

# Search (filters by arc to avoid cross-arc contamination)
echoes search "primo incontro" --arc bloom
echoes search "Alice" --type entities --arc bloom
```

### Environment Variables

```bash
# Custom embedding model (default: paraphrase-multilingual-MiniLM-L12-v2)
export ECHOES_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# HuggingFace token for gated models
export HF_TOKEN=hf_xxx

# Gemini API key for entity/relation extraction (optional)
# Get your key at https://aistudio.google.com/apikey
export GEMINI_API_KEY=your_api_key
```

### MCP Server

Configure in your MCP client (e.g., Claude Desktop, Kiro CLI):

```json
{
  "mcpServers": {
    "echoes": {
      "command": "echoes-mcp-server",
      "cwd": "/path/to/timeline"
    }
  }
}
```

Or with uvx (no installation required):

```json
{
  "mcpServers": {
    "echoes": {
      "command": "uvx",
      "args": ["echoes-mcp-server"],
      "cwd": "/path/to/timeline"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `words-count` | Count words and statistics in a markdown file |
| `index` | Index timeline content into LanceDB |
| `search-semantic` | Semantic search on chapters |
| `search-entities` | Search characters, locations, events |
| `search-relations` | Search relationships between entities |
| `stats` | Get aggregate statistics |

## Available Prompts

The server provides dynamic prompts that load templates from `../.github/.kiro/prompts/` and optionally append timeline-specific overrides from `./.kiro/prompts/`.

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `new-chapter` | arc, chapter | Create a new chapter for a timeline arc |
| `revise-chapter` | arc, chapter | Revise an existing chapter |
| `expand-chapter` | arc, chapter, target | Expand a chapter to target word count |
| `new-character` | name | Create a new character sheet |
| `new-episode` | arc, episode | Create a new episode outline |
| `new-arc` | name | Create a new story arc |
| `revise-arc` | arc | Review and fix an entire arc |

Prompts support placeholder substitution (`{ARC}`, `{CHAPTER}`, `{TIMELINE}`, etc.) and validate arguments (e.g., arc must exist, chapter must be a number).

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/echoes-io/mcp-server.git
cd mcp-server

# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv with Python 3.13 (required for spaCy compatibility)
uv venv --python 3.13

# Install dependencies
uv sync --all-extras

# The spaCy model downloads automatically on first use, or install manually:
uv pip install https://github.com/explosion/spacy-models/releases/download/it_core_news_lg-3.8.0/it_core_news_lg-3.8.0-py3-none-any.whl
```

### Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/
```

### Demo

Test with real timeline content:

```bash
# Create symlinks to timeline repos (adjust paths as needed)
cd demo
ln -s ../../timeline-anima/content anima
ln -s ../../timeline-eros/content eros

# Run demo
uv run python demo/run_demo.py
```

Example output:
```
============================================================
📚 Timeline: ANIMA
============================================================
📖 Chapters found: 55
📝 Total words: 199,519
📁 Arcs: ['anima', 'matilde']
👤 POVs: ['nic']

============================================================
📚 Timeline: EROS
============================================================
📖 Chapters found: 465
📝 Total words: 733,034
📁 Arcs: ['ale', 'ele', 'gio', 'ro', 'work']
👤 POVs: ['Ele', 'Nic', 'ale', 'angi', 'gio', 'nic', 'ro', 'vi']

============================================================
🔍 NER Demo (Named Entity Recognition)
============================================================
📄 Sample: anima/ep01/ch001
🏷️  Entities found: 33
   LOC: Malpensa, Terminal 2
   ORG: LinkedIn, Ryanair
   PER: GioGio, Cristo
```

### Project Structure

```
src/echoes_mcp/
├── __init__.py          # Package version
├── cli.py               # CLI interface (click)
├── server.py            # MCP server
├── database/
│   ├── lancedb.py       # LanceDB operations
│   └── schemas.py       # Pydantic schemas
├── indexer/
│   ├── scanner.py       # Filesystem scanner
│   ├── extractor.py     # Entity extraction (Gemini/spaCy)
│   ├── embeddings.py    # Embedding models
│   └── spacy_utils.py   # spaCy with auto-download
├── prompts/
│   ├── handlers.py      # Prompt loading and MCP integration
│   ├── substitution.py  # Placeholder replacement
│   └── validation.py    # Arc/argument validation
└── tools/
    ├── words_count.py   # Word counting
    ├── stats.py         # Statistics
    ├── search.py        # Search operations
    └── index.py         # Indexing tool

demo/
├── run_demo.py          # Demo script
├── anima -> ...         # Symlink to timeline-anima/content
└── eros -> ...          # Symlink to timeline-eros/content
```

### Tech Stack

| Purpose | Tool |
|---------|------|
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Linter/Formatter | [Ruff](https://docs.astral.sh/ruff/) |
| Type checker | [mypy](https://mypy-lang.org/) |
| Testing | [pytest](https://pytest.org/) |
| Vector DB | [LanceDB](https://lancedb.com/) |
| Embeddings | [sentence-transformers](https://sbert.net/) |
| NER | [spaCy](https://spacy.io/) (Italian model) |
| Entity Extraction | [Gemini 3 Flash](https://ai.google.dev/) (primary) / spaCy (fallback) |
| Knowledge Graph | [LlamaIndex](https://www.llamaindex.ai/) |

### Node.js Comparison

If you're coming from Node.js:

| Node/npm | Python/uv |
|----------|-----------|
| `npm install` | `uv sync` |
| `npm add pkg` | `uv add pkg` |
| `npm run test` | `uv run pytest` |
| `npx cmd` | `uv run cmd` |
| `package.json` | `pyproject.toml` |
| `node_modules/` | `.venv/` |
| Biome | Ruff |
| Vitest | pytest |

## License

MIT

---

Part of the [Echoes](https://github.com/echoes-io) project - a multi-POV digital storytelling platform.

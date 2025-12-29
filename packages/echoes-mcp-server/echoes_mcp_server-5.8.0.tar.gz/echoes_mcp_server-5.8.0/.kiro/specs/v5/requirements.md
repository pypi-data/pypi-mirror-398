# Echoes MCP Server v5 - Complete Specification

## Executive Summary

Riscrittura completa del mcp-server da TypeScript a **Python** per accedere all'ecosistema ML/NLP superiore (PropertyGraphIndex, spaCy, sentence-transformers). L'obiettivo è creare un sistema di **Narrative Knowledge Graph** che comprenda profondamente personaggi, luoghi, eventi e relazioni nelle storie.

---

## Problem Statement

Il mcp-server TypeScript attuale ha limitazioni fondamentali:
- **Ecosistema ML limitato**: No PropertyGraphIndex, NER scarso per italiano, fine-tuning complesso
- **GraphRAG custom insufficiente**: Relazioni superficiali, no entity extraction con LLM
- **Architettura confusa**: Separazione tracker/rag poco chiara, dati inconsistenti
- **Qualità non ottimale**: La comprensione narrativa è il cuore del progetto e richiede strumenti migliori

---

## Key Decisions

### 1. Linguaggio: Python
**Motivazione**: L'ecosistema Python per ML/NLP è nettamente superiore:
- `llama-index` con PropertyGraphIndex nativo
- `spaCy` con modello italiano (`it_core_news_lg`)
- `sentence-transformers` per fine-tuning embeddings
- Librerie mature e ben documentate

### 2. Database: LanceDB only (no SQLite)
**Motivazione**: 
- LanceDB supporta sia vector search che metadata filtering
- File-based e committabile nel repository
- Statistiche calcolabili in-memory (performante per 1000 capitoli)
- Un solo database semplifica l'architettura

### 3. Knowledge Graph: PropertyGraphIndex di LlamaIndex
**Motivazione**:
- Estrazione automatica entità e relazioni con LLM
- Schema configurabile per narrativa (CHARACTER, LOCATION, EVENT, etc.)
- Retrieval sofisticato (synonym, vector, cypher-like)
- Supporto nativo per graph traversal

### 4. Embedding Model: EmbeddingGemma o multilingual-e5
**Motivazione**:
- **EmbeddingGemma** (308M params): Best-in-class sotto 500M, 100+ lingue, ~200MB con quantizzazione
- **multilingual-e5-base** (278M params): Ottimo per italiano, ben testato
- Entrambi supportano italiano nativamente
- Possibilità di fine-tuning futuro su dominio narrativo

### 5. NER: spaCy italiano
**Motivazione**:
- Modello `it_core_news_lg` ottimizzato per italiano
- Estrazione entità (PER, LOC, ORG) accurata
- Integrazione con pipeline LlamaIndex

### 6. Interfaccia: CLI + MCP Server
**Motivazione**:
- CLI per uso diretto e scripting
- MCP Server per integrazione con Kiro CLI
- Logica condivisa tra le due interfacce

---

## Architecture

### Project Structure

```
echoes-mcp-server/
├── src/
│   └── echoes_mcp/
│       ├── __init__.py
│       ├── cli.py                 # CLI entry point (click)
│       ├── server.py              # MCP server entry point
│       ├── config.py              # Configuration management
│       ├── database/
│       │   ├── __init__.py
│       │   ├── lancedb.py         # LanceDB connection & operations
│       │   └── schemas.py         # Pydantic schemas for tables
│       ├── indexer/
│       │   ├── __init__.py
│       │   ├── scanner.py         # Filesystem scanner
│       │   ├── extractor.py       # PropertyGraphIndex setup
│       │   ├── embeddings.py      # Embedding model wrapper
│       │   └── ner.py             # spaCy NER italiano
│       └── tools/
│           ├── __init__.py
│           ├── index.py           # index tool
│           ├── search.py          # search-semantic, search-entities
│           ├── relations.py       # search-relations
│           ├── stats.py           # stats tool
│           └── words_count.py     # words-count tool
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── test_indexer.py
│   ├── test_search.py
│   └── test_tools.py
├── pyproject.toml                 # Project config (uv/poetry)
├── README.md
└── .github/
    └── workflows/
        ├── ci.yml                 # Test & lint
        └── release.yml            # Semantic release to PyPI
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     INDEXING PHASE                          │
│              (on-demand via CLI/MCP o GitHub Action)        │
├─────────────────────────────────────────────────────────────┤
│  1. Scan content/*.md (filesystem scanner)                  │
│  2. Parse frontmatter + content                             │
│  3. Per ogni capitolo:                                      │
│     a. Estrai entità con spaCy + LLM                       │
│     b. Estrai relazioni con PropertyGraphIndex             │
│     c. Genera embeddings (EmbeddingGemma/E5)               │
│     d. Calcola word count e statistiche                    │
│  4. Salva tutto in LanceDB                                  │
│  5. Aggiorna hash per change detection                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    LanceDB (committato)                     │
├─────────────────────────────────────────────────────────────┤
│  chapters.lance                                             │
│  ├── id, file_path, file_hash                              │
│  ├── arc, episode, chapter, pov, title                     │
│  ├── content (testo pulito)                                │
│  ├── word_count, char_count, paragraph_count               │
│  ├── vector (768 dim embedding)                            │
│  ├── entities[] (riferimenti a entities.lance)             │
│  └── indexed_at                                            │
│                                                             │
│  entities.lance                                             │
│  ├── id, name, type (CHARACTER/LOCATION/EVENT/OBJECT)      │
│  ├── description, aliases[]                                │
│  ├── vector (embedding nome+descrizione)                   │
│  ├── chapters[] (dove appare)                              │
│  └── first_appearance                                      │
│                                                             │
│  relations.lance                                            │
│  ├── id, source_entity, target_entity                      │
│  ├── type (LOVES/KNOWS/LOCATED_IN/CAUSES/etc.)            │
│  ├── description, weight                                   │
│  └── chapters[] (dove appare)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    QUERY PHASE                              │
│                 (runtime via CLI/MCP)                       │
├─────────────────────────────────────────────────────────────┤
│  Tools disponibili:                                         │
│  - words-count: conta parole da file markdown              │
│  - index: indicizza timeline (incrementale o full)         │
│  - search-semantic: ricerca semantica su capitoli          │
│  - search-entities: trova personaggi/luoghi/eventi         │
│  - search-relations: "chi ama chi?", relazioni             │
│  - stats: statistiche aggregate                            │
└─────────────────────────────────────────────────────────────┘
```

---

## LanceDB Schemas

### chapters.lance

```python
class ChapterRecord(BaseModel):
    # Identificazione
    id: str                      # "arc1:ep01:ch001"
    file_path: str               # "content/arc1/ep01/ch001.md"
    file_hash: str               # SHA256 per change detection
    
    # Gerarchia
    arc: str                     # "arc1"
    episode: int                 # 1
    chapter: int                 # 1
    
    # Metadati (da frontmatter)
    pov: str                     # "Alice"
    title: str                   # "L'incontro"
    location: str | None         # "Castello"
    date: str | None             # Data narrativa
    
    # Contenuto
    content: str                 # Testo pulito (no frontmatter/markdown)
    excerpt: str | None          # Riassunto breve
    
    # Statistiche
    word_count: int
    char_count: int
    paragraph_count: int
    
    # RAG
    vector: list[float]          # 768 dim embedding
    entities: list[str]          # ["character:alice", "location:castello"]
    
    # Metadata
    indexed_at: int              # Unix timestamp
```

### entities.lance

```python
class EntityRecord(BaseModel):
    id: str                      # "character:alice"
    name: str                    # "Alice"
    type: Literal["CHARACTER", "LOCATION", "EVENT", "OBJECT", "EMOTION"]
    description: str             # "Protagonista, ragazza coraggiosa..."
    aliases: list[str]           # ["la ragazza", "lei"]
    
    # RAG
    vector: list[float]          # Embedding di nome+descrizione
    
    # Riferimenti
    chapters: list[str]          # Chapter IDs dove appare
    chapter_count: int           # Numero di capitoli
    first_appearance: str        # Primo chapter ID
    
    # Metadata
    indexed_at: int
```

### relations.lance

```python
class RelationRecord(BaseModel):
    id: str                      # "rel:alice:loves:bob"
    source_entity: str           # "character:alice"
    target_entity: str           # "character:bob"
    type: str                    # "LOVES", "KNOWS", "LOCATED_IN", etc.
    description: str             # "Alice si innamora di Bob..."
    weight: float                # 0.0-1.0 (frequenza/importanza)
    
    # Riferimenti
    chapters: list[str]          # Chapter IDs dove appare
    
    # Metadata
    indexed_at: int
```

---

## Entity & Relation Types

### Entity Types (per narrativa italiana)

```python
ENTITY_TYPES = [
    "CHARACTER",    # Personaggi (protagonisti, antagonisti, secondari)
    "LOCATION",     # Luoghi (città, edifici, stanze)
    "EVENT",        # Eventi significativi (incontri, battaglie, rivelazioni)
    "OBJECT",       # Oggetti importanti (artefatti, lettere, armi)
    "EMOTION",      # Stati emotivi ricorrenti (paura, amore, rabbia)
]
```

### Relation Types (per narrativa)

```python
RELATION_TYPES = [
    # Relazioni tra personaggi
    "LOVES",        # Amore romantico
    "HATES",        # Odio
    "KNOWS",        # Conoscenza
    "RELATED_TO",   # Parentela
    "FRIENDS_WITH", # Amicizia
    "ENEMIES_WITH", # Inimicizia
    
    # Relazioni spaziali
    "LOCATED_IN",   # Personaggio/evento in luogo
    "LIVES_IN",     # Residenza
    "TRAVELS_TO",   # Spostamento
    
    # Relazioni temporali
    "HAPPENS_BEFORE",  # Evento precede altro
    "HAPPENS_AFTER",   # Evento segue altro
    "CAUSES",          # Evento causa altro
    
    # Relazioni con oggetti
    "OWNS",         # Possesso
    "USES",         # Utilizzo
    "SEEKS",        # Ricerca
]
```

---

## MCP Tools Specification

### 1. words-count

Conta parole e statistiche da file markdown.

```python
# Input
{
    "file": str  # Path al file markdown
}

# Output
{
    "words": int,
    "characters": int,
    "paragraphs": int,
    "reading_time_minutes": float
}
```

**Comportamento**:
- Rimuove frontmatter YAML
- Rimuove sintassi markdown (headers, links, code blocks, etc.)
- Conta solo testo effettivo

### 2. index

Indicizza contenuto timeline in LanceDB.

```python
# Input
{
    "content_path": str,           # Path alla directory content/
    "force": bool = False,         # Force full re-index
    "arc": str | None = None,      # Indicizza solo questo arc
    "episode": int | None = None,  # Indicizza solo questo episodio
}

# Output
{
    "indexed": int,    # Nuovi capitoli indicizzati
    "updated": int,    # Capitoli aggiornati
    "deleted": int,    # Capitoli rimossi
    "entities": int,   # Entità estratte
    "relations": int,  # Relazioni estratte
    "duration_seconds": float
}
```

**Comportamento**:
- Scan ricorsivo di content/
- Change detection via file hash
- Estrazione entità con spaCy + LLM
- Estrazione relazioni con PropertyGraphIndex
- Generazione embeddings
- Salvataggio incrementale in LanceDB

### 3. search-semantic

Ricerca semantica su capitoli.

```python
# Input
{
    "query": str,                  # Query in linguaggio naturale
    "arc": str | None = None,      # Filtro arc
    "episode": int | None = None,  # Filtro episodio
    "pov": str | None = None,      # Filtro POV
    "limit": int = 10,             # Max risultati
}

# Output
{
    "results": [
        {
            "id": str,
            "title": str,
            "pov": str,
            "arc": str,
            "episode": int,
            "chapter": int,
            "score": float,
            "excerpt": str,        # Preview del contenuto
        }
    ]
}
```

### 4. search-entities

Cerca entità (personaggi, luoghi, etc.).

```python
# Input
{
    "query": str | None = None,    # Ricerca semantica
    "name": str | None = None,     # Ricerca esatta per nome
    "type": str | None = None,     # Filtro tipo (CHARACTER, LOCATION, etc.)
    "limit": int = 10,
}

# Output
{
    "results": [
        {
            "id": str,
            "name": str,
            "type": str,
            "description": str,
            "aliases": list[str],
            "chapter_count": int,
            "score": float,        # Se ricerca semantica
        }
    ]
}
```

### 5. search-relations

Cerca relazioni tra entità.

```python
# Input
{
    "entity": str | None = None,   # Trova relazioni di questa entità
    "source": str | None = None,   # Entità sorgente
    "target": str | None = None,   # Entità destinazione
    "type": str | None = None,     # Tipo relazione
    "query": str | None = None,    # Ricerca semantica su descrizione
    "limit": int = 10,
}

# Output
{
    "results": [
        {
            "id": str,
            "source": {"id": str, "name": str, "type": str},
            "target": {"id": str, "name": str, "type": str},
            "type": str,
            "description": str,
            "weight": float,
            "chapter_count": int,
        }
    ]
}
```

### 6. stats

Statistiche aggregate.

```python
# Input
{
    "arc": str | None = None,
    "episode": int | None = None,
    "pov": str | None = None,
}

# Output
{
    "chapters": int,
    "words": int,
    "avg_words_per_chapter": float,
    "min_words": int,
    "max_words": int,
    "unique_povs": int,
    "pov_distribution": dict[str, int],
    "entities": {
        "total": int,
        "characters": int,
        "locations": int,
        "events": int,
    },
    "relations": int,
}
```

---

## CLI Interface

```bash
# Indexing
echoes index ./content                    # Index incrementale
echoes index ./content --force            # Full re-index
echoes index ./content --arc arc1         # Solo arc1

# Search
echoes search "Alice incontra Bob"        # Semantic search
echoes search "Alice" --type entities     # Cerca entità
echoes search "Alice" --type relations    # Relazioni di Alice

# Stats
echoes stats                              # Statistiche globali
echoes stats --arc arc1                   # Statistiche arc1
echoes stats --pov Alice                  # Statistiche POV Alice

# Words count
echoes words-count ./content/arc1/ep01/ch001.md

# MCP Server
echoes serve                              # Avvia MCP server
```

---

## Python Tooling (equivalenti Node.js)

| Node.js | Python | Scopo |
|---------|--------|-------|
| npm/pnpm | **uv** | Package manager (velocissimo) |
| TypeScript | **Python 3.11+** con type hints | Linguaggio |
| Biome | **Ruff** | Linter + formatter (velocissimo) |
| Vitest | **pytest** | Testing |
| semantic-release | **python-semantic-release** | Versioning automatico |
| npm publish | **PyPI** (via uv/twine) | Package registry |
| tsconfig.json | **pyproject.toml** | Configurazione progetto |
| Zod | **Pydantic** | Schema validation |

### pyproject.toml

```toml
[project]
name = "echoes-mcp-server"
version = "0.0.0"  # Gestito da semantic-release
description = "MCP server for Echoes storytelling platform with Narrative Knowledge Graph"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Zweer", email = "n.olivieriachille@gmail.com"}
]
keywords = ["echoes", "mcp", "storytelling", "knowledge-graph", "rag"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "click>=8.1",
    "mcp>=1.0",
    "lancedb>=0.4",
    "llama-index>=0.10",
    "llama-index-embeddings-huggingface>=0.2",
    "sentence-transformers>=2.2",
    "spacy>=3.7",
    "pydantic>=2.0",
    "rich>=13.0",  # Pretty CLI output
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.8",
    "python-semantic-release>=9.0",
]

[project.scripts]
echoes = "echoes_mcp.cli:cli"
echoes-mcp-server = "echoes_mcp.server:main"

[project.urls]
Homepage = "https://github.com/echoes-io/mcp-server"
Repository = "https://github.com/echoes-io/mcp-server"
Issues = "https://github.com/echoes-io/mcp-server/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/echoes_mcp"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["src/echoes_mcp"]
branch = true

[tool.coverage.report]
fail_under = 90

[tool.mypy]
python_version = "3.11"
strict = true

[tool.semantic_release]
version_variable = "src/echoes_mcp/__init__.py:__version__"
version_toml = ["pyproject.toml:project.version"]
branch = "main"
upload_to_pypi = true
build_command = "pip install build && python -m build"
```

---

## GitHub Actions

### CI (.github/workflows/ci.yml)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Lint with Ruff
        run: uv run ruff check .
      
      - name: Type check with mypy
        run: uv run mypy src/
      
      - name: Test with pytest
        run: uv run pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### Release (.github/workflows/release.yml)

```yaml
name: Release

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency: release
    permissions:
      id-token: write
      contents: write
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Semantic Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: uv run semantic-release publish
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

---

## Kiro CLI Configuration

```json
{
  "mcpServers": {
    "echoes": {
      "command": "echoes-mcp-server",
      "cwd": "/path/to/timeline-pulse"
    }
  }
}
```

Oppure con uvx (senza installazione globale):

```json
{
  "mcpServers": {
    "echoes": {
      "command": "uvx",
      "args": ["echoes-mcp-server"],
      "cwd": "/path/to/timeline-pulse"
    }
  }
}
```

---

## Migration Plan

### Phase 1: Setup progetto Python
- [ ] Creare struttura progetto con pyproject.toml
- [ ] Configurare uv, ruff, pytest, mypy
- [ ] Setup GitHub Actions (CI + Release)
- [ ] Creare README.md

### Phase 2: Core functionality
- [ ] Implementare LanceDB wrapper con schemas
- [ ] Implementare filesystem scanner
- [ ] Implementare words-count tool
- [ ] Implementare stats tool

### Phase 3: Indexing
- [ ] Integrare spaCy per NER italiano
- [ ] Configurare PropertyGraphIndex con schema narrativo
- [ ] Implementare embedding generation
- [ ] Implementare index tool con change detection

### Phase 4: Search
- [ ] Implementare search-semantic
- [ ] Implementare search-entities
- [ ] Implementare search-relations

### Phase 5: Integration
- [ ] Implementare CLI con click
- [ ] Implementare MCP server
- [ ] Testing end-to-end su timeline reale
- [ ] Pubblicazione su PyPI

### Phase 6: Cleanup
- [ ] Archiviare codice TypeScript
- [ ] Aggiornare documentazione
- [ ] Migrare timeline esistenti

---

## Quality Standards

- **Test coverage**: ≥90%
- **Type hints**: 100% (mypy strict)
- **Linting**: Ruff con zero warnings
- **Documentation**: Docstrings per tutte le funzioni pubbliche
- **Commit messages**: Conventional Commits per semantic-release

---

## Open Questions (da decidere durante implementazione)

1. **LLM per entity extraction**: OpenAI, Gemini, o locale (Ollama)?
2. **Embedding model finale**: EmbeddingGemma vs multilingual-e5?
3. **Fine-tuning**: Vale la pena fine-tunare embeddings su corpus italiano?
4. **Graph storage**: Solo LanceDB o anche export per visualizzazione?

---

## References

- [LlamaIndex PropertyGraphIndex](https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/)
- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [spaCy Italian Models](https://spacy.io/models/it)
- [EmbeddingGemma](https://huggingface.co/blog/embeddinggemma)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [uv Package Manager](https://docs.astral.sh/uv/)
- [Ruff Linter](https://docs.astral.sh/ruff/)

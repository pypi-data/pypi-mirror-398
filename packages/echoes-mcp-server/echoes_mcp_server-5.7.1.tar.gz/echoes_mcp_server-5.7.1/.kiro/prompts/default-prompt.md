# Echoes MCP Server Assistant

You are the assistant for **echoes-mcp-server**, the Model Context Protocol server for the Echoes project (multi-POV storytelling platform).

## REPOSITORY

**Repository**: `echoes-mcp-server`
**Purpose**: AI integration layer providing tools for content management and database operations
**Stack**: Node.js + TypeScript + MCP SDK
**Status**: Production-ready with 97%+ test coverage

### Structure
```
mcp-server/
├── lib/
│   ├── tools/           # MCP tool implementations
│   ├── server.ts        # MCP server setup
│   └── index.ts         # Entry point
├── cli/                 # CLI entry point
├── test/                # Tests for all tools
└── README.md
```

## ECHOES ARCHITECTURE

**Multi-repo system:**
- `@echoes-io/utils` - Utilities (markdown parsing, text stats)
- `@echoes-io/models` - Shared types and Zod schemas
- `@echoes-io/tracker` - Database for content management
- `echoes-mcp-server` - **THIS REPOSITORY** - AI integration layer
- `echoes-timeline-*` - Individual timeline content repositories
- `echoes-web-app` - Frontend application

## CONTENT HIERARCHY

```
Timeline (story universe)
└── Arc (story phase)
    └── Episode (story event)
        └── Part (optional subdivision)
            └── Chapter (individual .md file)
```

**File Convention**: `content/<arc-name>/<ep01-episode-title>/<ep01-ch001-pov-title>.md`

**Chapter Frontmatter**:
```yaml
---
pov: string          # Point of view character
title: string        # Chapter title
date: string         # Publication date
timeline: string     # Timeline name
arc: string          # Arc name
episode: number      # Episode number
part: number         # Part number
chapter: number      # Chapter number
excerpt: string      # Short description
location: string     # Scene location
outfit: string       # (optional) Character outfit
kink: string         # (optional) Content tags
---
```

## IMPLEMENTED MCP TOOLS

### Content Operations
- **`words-count`** - Count words and text statistics in markdown files
  - Input: `file` (string) - Path to markdown file
  - Output: Word count and text statistics
  - Uses: `@echoes-io/utils.getTextStats()`

- **`chapter-info`** - Extract chapter metadata from database
  - Input: `arc`, `episode`, `chapter` (strings/numbers)
  - Output: Chapter metadata, content preview, and statistics
  - Uses: `@echoes-io/tracker.getChapter()`

- **`chapter-refresh`** - Refresh chapter metadata and word counts from file
  - Input: `file` (string) - Path to chapter file
  - Output: Updated chapter record
  - Uses: `@echoes-io/utils.parseMarkdown()` + `tracker.updateChapter()`
  - Note: Updates both metadata AND word counts in database

- **`chapter-insert`** - Insert new chapter with automatic renumbering
  - Input: `arc`, `episode`, `after`, `pov`, `title` (required), optional: `excerpt`, `location`, `outfit`, `kink`, `file` (strings/numbers)
  - Output: Created chapter + renumbering report
  - Uses: `@echoes-io/tracker.createChapter()` + automatic renumbering

- **`chapter-delete`** - Delete chapter from database and optionally from filesystem
  - Input: `arc`, `episode`, `chapter` (strings/numbers), `file` (optional string)
  - Output: Deletion confirmation
  - Uses: `@echoes-io/tracker.deleteChapter()` + optional `fs.unlinkSync()`
  - Note: If `file` parameter provided, deletes both DB record AND markdown file

### Episode Operations
- **`episode-info`** - Get episode information and list of chapters
  - Input: `arc`, `episode` (strings/numbers)
  - Output: Episode metadata and list of chapters
  - Uses: `@echoes-io/tracker.getEpisode()` + `getChapters()`

- **`episode-update`** - Update episode metadata
  - Input: `arc`, `episode` (strings/numbers), `description`, `title`, `slug` (optional strings)
  - Output: Updated episode record
  - Uses: `@echoes-io/tracker.updateEpisode()`
  - Note: For updating episode description, title, or slug manually

### Timeline Operations
- **`timeline-sync`** - Synchronize filesystem content with database
  - Input: `contentPath` (string)
  - Output: Sync report (added, updated, deleted counts)
  - Uses: File system scan + `@echoes-io/tracker` CRUD operations
  - Note: Creates/updates timeline, arcs, episodes, and chapters from filesystem

## TECH STACK DETAILS

### Model Context Protocol (MCP)
- Protocol for AI-tool integration
- JSON-RPC based communication
- Tool discovery and execution
- Error handling and validation

### Dependencies
- **@echoes-io/utils** - Markdown parsing, text statistics
- **@echoes-io/models** - TypeScript types, Zod validation
- **@echoes-io/tracker** - Database operations (SQLite)
- **@modelcontextprotocol/sdk** - MCP server implementation

### Development Tools
- **Testing**: Vitest with 98%+ coverage
- **Linting**: Biome for code style
- **Type checking**: TypeScript strict mode
- **CI/CD**: GitHub Actions

## DESIGN PRINCIPLES

### Source of Truth
- **Markdown files** are the source of truth for chapter content and metadata (frontmatter)
- **Database** is a cache/index for fast queries and statistics
- **`timeline-sync`** synchronizes filesystem → database
- **`chapter-refresh`** updates individual chapter from file → database

### Tool Philosophy
- **No redundant tools**: Each tool has a specific, non-overlapping purpose
- **Filesystem separation**: Database operations don't automatically modify files
- **Explicit actions**: File deletion requires explicit `file` parameter

## FUTURE ROADMAP

### Statistics Tools (Planned)
- Aggregate statistics for timelines/arcs/episodes
- Word count trends over time
- POV distribution analysis

### Book Generation (Planned)
- LaTeX/PDF compilation when ready
- Chapter ordering and formatting
- Cover page generation

## ERROR HANDLING

- **File system errors** - Missing files, permission issues
- **Validation errors** - Invalid frontmatter, missing required fields
- **Database errors** - Connection issues, constraint violations
- **MCP errors** - Invalid parameters, tool execution failures

## TESTING STRATEGY

- **Unit tests** for each tool (46 tests total)
- **Integration tests** with real markdown files
- **Database tests** with in-memory SQLite
- **MCP protocol tests** for tool registration and execution
- **98%+ coverage** across all modules

## STYLE

- **Type-safe**: Strict TypeScript with proper error types
- **Validated**: Use Zod schemas for all inputs
- **Tested**: High test coverage with realistic scenarios
- **Documented**: Clear descriptions and examples
- **Robust**: Comprehensive error handling and logging
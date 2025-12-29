# MCP Server Consolidation Requirements

## Overview

Consolidate all Echoes libraries into a single MCP server project using Mastra.ai framework to simplify development, debugging, and deployment.

## Current State

**Separate repositories:**
- `@echoes-io/models` - TypeScript types + Zod schemas
- `@echoes-io/utils` - Markdown parsing, text statistics
- `@echoes-io/tracker` - SQLite database with Kysely
- `@echoes-io/rag` - Vector embeddings and semantic search
- `@echoes-io/mcp-server` - MCP tools orchestration

**Problems:**
- Complex debugging across 5 repositories
- Dependency management overhead
- Slow development cycle
- No external reuse of individual packages

## Target State

**Single consolidated project:**
```
mcp-server/
├── src/
│   ├── types/          # from @echoes-io/models
│   ├── utils/          # from @echoes-io/utils
│   ├── storage/        # from @echoes-io/tracker
│   ├── rag/            # replaced by Mastra GraphRAG
│   └── tools/          # MCP tools implementation
├── .kiro/
│   └── specs/
└── package.json        # unified dependencies
```

## Requirements

### R1: Framework Migration
- **MUST** migrate to Mastra.ai framework
- **MUST** use Mastra's GraphRAG instead of custom RAG
- **MUST** leverage Mastra's MCP integration
- **MUST** use Mastra's workflow engine for orchestration

### R2: Code Consolidation
- **MUST** merge all existing libraries into single project
- **MUST** maintain existing MCP tool interfaces
- **MUST** preserve all current functionality
- **SHOULD** improve performance with GraphRAG

### R3: Project Structure
```
src/
├── types/
│   ├── content.ts      # Timeline, Arc, Episode, Chapter types
│   ├── frontmatter.ts  # YAML schema validation
│   └── index.ts
├── utils/
│   ├── markdown.ts     # Parsing and processing
│   ├── statistics.ts   # Word count, reading time
│   ├── paths.ts        # File path generation
│   └── index.ts
├── storage/
│   ├── database.ts     # SQLite with Kysely
│   ├── migrations/     # Database schema
│   └── index.ts
├── rag/
│   ├── graph.ts        # Mastra GraphRAG implementation
│   ├── embeddings.ts   # Vector operations
│   └── index.ts
└── tools/
    ├── content.ts      # chapter-info, episode-info, words-count
    ├── sync.ts         # timeline-sync, chapter-refresh
    ├── search.ts       # rag-search, rag-context, rag-characters
    ├── stats.ts        # statistics tools
    └── index.ts
```

### R4: MCP Tools Compatibility
**MUST** maintain exact same tool interfaces:

**Content Operations:**
- `chapter-info({ timeline, arc, episode, chapter })`
- `episode-info({ timeline, arc, episode })`
- `words-count({ filePath })`

**Database Sync:**
- `timeline-sync({ timeline, contentPath })`
- `chapter-refresh({ timeline, arc, episode, chapter, filePath })`

**RAG Operations:**
- `rag-search({ timeline, query, topK?, characters?, allCharacters? })`
- `rag-context({ timeline, query, topK?, characters?, allCharacters? })`
- `rag-characters({ timeline, character })`

**Statistics:**
- `stats({ timeline?, arc?, episode? })`

### R5: GraphRAG Enhancement
- **MUST** replace simple vector search with GraphRAG
- **MUST** maintain character filtering capabilities
- **SHOULD** improve context discovery through graph traversal
- **SHOULD** provide better semantic relationships

### R6: Development Experience
- **MUST** enable single-project debugging
- **MUST** support hot reload for all components
- **MUST** unify dependency management
- **SHOULD** reduce build time

### R7: Migration Strategy
1. **Phase 1:** Setup Mastra.ai project structure
2. **Phase 2:** Migrate types and utils (no external dependencies)
3. **Phase 3:** Migrate storage layer with database
4. **Phase 4:** Replace RAG with Mastra GraphRAG
5. **Phase 5:** Integrate MCP tools with Mastra framework
6. **Phase 6:** Test compatibility with existing timeline agents
7. **Phase 7:** Archive old repositories

## Technical Specifications

### Dependencies
```json
{
  "@mastra/core": "latest",
  "@mastra/rag": "latest", 
  "kysely": "^0.27.0",
  "better-sqlite3": "^9.0.0",
  "zod": "^3.22.0"
}
```

### Configuration
- Use Mastra's configuration system
- Environment variables for timeline-specific settings
- Database connection pooling
- Vector store configuration

### Performance Requirements
- **MUST** maintain sub-second response for MCP tools
- **SHOULD** improve RAG query performance with GraphRAG
- **MUST** support concurrent operations
- **SHOULD** optimize memory usage

## Success Criteria

### Functional
- [ ] All existing MCP tools work identically
- [ ] GraphRAG provides better context than current RAG
- [ ] Timeline agents work without changes
- [ ] Database operations maintain consistency

### Non-Functional  
- [ ] Single-project debugging works
- [ ] Hot reload functions across all components
- [ ] Build time reduced by >50%
- [ ] Memory usage optimized
- [ ] Development velocity increased

## Risks & Mitigations

**Risk:** Mastra.ai framework limitations
**Mitigation:** Prototype core functionality first

**Risk:** GraphRAG performance regression
**Mitigation:** A/B test against current RAG

**Risk:** Breaking changes in MCP interface
**Mitigation:** Comprehensive integration tests

**Risk:** Data migration issues
**Mitigation:** Backup existing databases, gradual migration

## Timeline

- **Week 1:** Mastra.ai prototype + types/utils migration
- **Week 2:** Storage layer + database migration  
- **Week 3:** GraphRAG implementation + testing
- **Week 4:** MCP tools integration + validation
- **Week 5:** Timeline agent compatibility testing
- **Week 6:** Production deployment + old repo archival

## Dependencies

- Mastra.ai framework stability
- Existing timeline repositories for testing
- Database backup procedures
- CI/CD pipeline updates

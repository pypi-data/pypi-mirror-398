# MCP Server Architecture

## Overview

The Echoes MCP Server provides both an MCP (Model Context Protocol) interface and a CLI interface for all tools.

## Structure

```
mcp-server/
├── cli/
│   └── index.ts          # CLI entry point (dual mode: MCP server or CLI commands)
├── src/
│   ├── server.ts         # MCP server setup and tool registration
│   ├── index.ts          # Main exports
│   ├── tools/            # Tool implementations
│   │   ├── index.ts      # Tool exports
│   │   ├── words-count.ts # Word counting tool
│   │   └── index-tracker.ts # Filesystem → database sync
│   ├── database/         # Database layer (Drizzle + sqlite-vec)
│   ├── rag/              # GraphRAG and embeddings
│   ├── utils/            # Utilities (markdown parsing, etc.)
│   └── types/            # TypeScript types and Zod schemas
└── test/
    └── tools/            # Tool tests
```

## Implemented Tools

### 1. words-count
- **Purpose**: Count words and text statistics in markdown files
- **Input**: `{ filePath: string, detailed?: boolean }`
- **Output**: Word count, characters, reading time, optional sentences/paragraphs
- **CLI**: `echoes-mcp-server words-count <file> [--detailed]`

### 2. index-tracker
- **Purpose**: Synchronize filesystem content with database
- **Input**: `{ timeline: string, contentPath: string }`
- **Output**: Scan results (scanned, added, updated, deleted counts)
- **CLI**: `echoes-mcp-server index-tracker <timeline> <content-path>`
- **Features**: 
  - Scans directory recursively for `.md` files
  - Parses frontmatter metadata
  - Creates timeline/arc/episode/chapter records in database
  - Handles missing metadata with path-based inference

### 5. rag-context
- **Purpose**: Retrieve full chapter content for AI context using semantic search
- **Input**: `{ timeline: string, query: string, maxChapters?: number, characters?: string[], allCharacters?: boolean, arc?: string, pov?: string }`
- **Output**: Full chapter content with metadata and performance metrics
- **CLI**: `echoes-mcp-server rag-context <timeline> "<query>" [options]`
- **Features**:
  - Returns complete chapter content for AI processing
  - Same filtering capabilities as rag-search
  - Context length calculation for token management
  - Optimized for AI context windows
  - Performance tracking and metadata preservation

## Dual Interface Pattern

Every tool follows this pattern:

### 1. Tool Implementation (`src/tools/tool-name.ts`)

```typescript
import { z } from 'zod';

// Input schema for validation
export const toolNameSchema = z.object({
  param1: z.string(),
  param2: z.boolean().optional()
});

export type ToolNameInput = z.infer<typeof toolNameSchema>;

// Output interface
export interface ToolNameOutput {
  result: string;
}

// Core implementation (used by both MCP and CLI)
export async function toolName(input: ToolNameInput): Promise<ToolNameOutput> {
  const validated = toolNameSchema.parse(input);
  // Implementation here
  return { result: 'done' };
}
```

### 2. MCP Registration (`src/server.ts`)

```typescript
// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'tool-name',
        description: 'Tool description',
        inputSchema: toolNameSchema,
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case 'tool-name':
      try {
        const result = await toolName(args as any);
        return {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        };
      } catch (error) {
        return {
          content: [{ type: 'text', text: `Error: ${error.message}` }],
          isError: true,
        };
      }
  }
});
```

### 3. CLI Command (`cli/index.ts`)

```typescript
switch (command) {
  case 'tool-name': {
    const param1 = args[0];
    const param2 = args.includes('--flag');
    
    if (!param1) {
      console.error('Usage: echoes-mcp-server tool-name <param1> [--flag]');
      process.exit(1);
    }
    
    try {
      const result = await toolName({ param1, param2 });
      console.log(JSON.stringify(result, null, 2));
    } catch (error) {
      console.error('Error:', error.message);
      process.exit(1);
    }
    break;
  }
}
```

### 4. Tests (`test/tools/tool-name.test.ts`)

```typescript
import { describe, it, expect } from 'vitest';
import { toolName } from '../../src/tools/tool-name.js';

describe('tool-name', () => {
  it('should work correctly', async () => {
    const result = await toolName({ param1: 'test' });
    expect(result.result).toBe('done');
  });
});
```

## Usage

### As MCP Server

```bash
# Run MCP server (stdio transport)
echoes-mcp-server

# Or with npx
npx @echoes-io/mcp-server
```

### As CLI

```bash
# Run CLI commands
echoes-mcp-server words-count file.md
echoes-mcp-server words-count file.md --detailed
echoes-mcp-server index-tracker timeline-name /path/to/content
echoes-mcp-server index-rag timeline-name /path/to/content
echoes-mcp-server index-rag timeline-name /path/to/content --arc arc1
echoes-mcp-server index-rag timeline-name /path/to/content --episode 1
echoes-mcp-server rag-search timeline-name "search query"
echoes-mcp-server rag-search timeline-name "Alice and Bob" --characters Alice,Bob --all-characters
echoes-mcp-server rag-search timeline-name "romantic scene" --arc arc1 --top-k 5
echoes-mcp-server rag-context timeline-name "context query" --max-chapters 3
echoes-mcp-server rag-context timeline-name "Alice conversation" --characters Alice --arc arc1
echoes-mcp-server help
```

## Adding New Tools

1. Create `src/tools/new-tool.ts` with schema, types, and implementation
2. Export from `src/tools/index.ts`
3. Register in `src/server.ts` (ListTools + CallTool handlers)
4. Add CLI command in `cli/index.ts`
5. Create tests in `test/tools/new-tool.test.ts`
6. Update help text in `cli/index.ts`

## Benefits

- **Single source of truth**: Core logic in tool implementation
- **Type safety**: Zod schemas validate inputs for both interfaces
- **Testability**: Test the core function directly
- **Flexibility**: Use as MCP server or standalone CLI
- **Consistency**: Same behavior in both modes

## Current Status

- ✅ **words-count**: Complete with tests (3 tests passing)
- ✅ **index-tracker**: Complete with tests (3 tests passing)
- ✅ **index-rag**: Complete with tests (5 tests passing)
- ✅ **rag-search**: Complete with tests (5 tests passing)
- ✅ **rag-context**: Complete with tests (5 tests passing)
- 🔄 **Character tools**: rag-characters (next to implement)
- 🔄 **Enhanced tools**: Additional functionality planned

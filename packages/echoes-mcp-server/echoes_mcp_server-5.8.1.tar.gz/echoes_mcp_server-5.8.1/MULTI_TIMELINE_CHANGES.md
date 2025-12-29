# Multi-Timeline Architecture Implementation

## Overview

Implemented multi-timeline support with isolated databases per timeline for better security and data separation.

## Architecture Changes

### Before
```
.github/
  tracker.db          # Single centralized database
  rag.db              # Single centralized RAG index
```

### After
```
echoes-io/
  .github/            # Server runs from here (must be cwd)
  timeline-eros/      # Private timeline repo
    tracker.db        # Timeline-specific database
    rag.db            # Timeline-specific RAG index
    content/...
  timeline-anima/     # Another private timeline
    tracker.db
    rag.db
    content/...
```

## Key Features

1. **Auto-discovery**: Server scans `../timeline-*` directories at startup
2. **Isolated databases**: Each timeline has its own tracker.db and rag.db in its repo
3. **Security**: Timeline repos can be private, only `.github` needs to be public
4. **Simplified API**: No need to pass `contentPath` - auto-discovered from timeline name
5. **Validation**: Server crashes if not run from `.github` directory

## Modified Files

### Core Server (`lib/server.ts`)
- Added `TimelineContext` interface with `{tracker, rag, contentPath}`
- `runServer()`: Auto-discovers timelines and creates Map<timeline, context>
- `createServer()`: Accepts timelines Map instead of single tracker/rag
- Tool handlers: Get context from Map based on timeline parameter

### Tool Schemas (removed `contentPath` parameter)
- `lib/tools/timeline-sync.ts`: Now only requires `timeline`
- `lib/tools/rag-index.ts`: Now only requires `timeline`
- `lib/tools/book-generate.ts`: Now only requires `timeline`

### Tests
- `test/server.test.ts`: Updated to use timelines Map
- `test/tools/rag-index.test.ts`: Added contentPath to test calls

### Documentation
- `README.md`: Updated with multi-timeline architecture section
- Added `cwd` requirement in configuration examples

## Benefits

1. **Privacy**: Each timeline's data stays in its own (potentially private) repo
2. **Isolation**: No risk of data leakage between timelines
3. **Simplicity**: Users only specify timeline name, not paths
4. **Scalability**: Easy to add/remove timelines by adding/removing directories
5. **Access Control**: Share only the timeline repos you want to share

## Migration Guide

### For Users

**Old configuration:**
```json
{
  "mcpServers": {
    "echoes": {
      "command": "echoes-mcp-server"
    }
  }
}
```

**New configuration:**
```json
{
  "mcpServers": {
    "echoes": {
      "command": "echoes-mcp-server",
      "cwd": "/path/to/echoes-io/.github"
    }
  }
}
```

### For Tool Calls

**Old:**
```javascript
await timelineSync({ 
  timeline: 'eros', 
  contentPath: '../timeline-eros/content' 
});
```

**New:**
```javascript
await timelineSync({ 
  timeline: 'eros'
  // contentPath auto-discovered
});
```

## Testing

Run from `.github` directory:
```bash
cd /path/to/echoes-io/.github
npx echoes-mcp-server
```

Server will:
1. Validate it's running from `.github`
2. Scan `../timeline-*` directories
3. Initialize tracker.db and rag.db for each timeline
4. Report number of timelines found

## Notes

- Test mode still uses in-memory databases
- Timeline directories must have a `content/` subdirectory to be recognized
- Database files are created in timeline directories, not in `.github`

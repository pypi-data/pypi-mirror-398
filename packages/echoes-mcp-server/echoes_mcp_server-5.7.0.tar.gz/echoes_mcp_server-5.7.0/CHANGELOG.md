## [4.1.1](https://github.com/echoes-io/mcp-server/compare/v4.1.0...v4.1.1) (2025-12-20)


### Bug Fixes

* :construction_worker: Fixing the release process ([50d13f4](https://github.com/echoes-io/mcp-server/commit/50d13f47d3578057f3ca2abc34a772dee8506d3e))

# [4.1.0](https://github.com/echoes-io/mcp-server/compare/v4.0.0...v4.1.0) (2025-12-20)


### Features

* add automatic timeline detection for CLI commands ([be58d0a](https://github.com/echoes-io/mcp-server/commit/be58d0ac37547f5ce6cebf0e114dce03e5cab274))

# [4.0.0](https://github.com/echoes-io/mcp-server/compare/v3.0.0...v4.0.0) (2025-12-19)


### Features

* :sparkles: Added the rag-context tool ([40c2133](https://github.com/echoes-io/mcp-server/commit/40c21334714bedcc3c90cbc1263997d01e4c4fcf))
* implement complete storage layer with Drizzle ORM and vector search ([0262331](https://github.com/echoes-io/mcp-server/commit/0262331aecffceaf75b113d1bef4f1391ce11dab))
* implement core types and markdown utilities with comprehensive tests ([61d0209](https://github.com/echoes-io/mcp-server/commit/61d02094afe204f4333bb4c816598444decd62c9))
* implement dual MCP/CLI interface with words-count tool ([fbfe0f9](https://github.com/echoes-io/mcp-server/commit/fbfe0f99aaeb31cf5067237aa149d40791f7f3ef))
* implement GraphRAG system with Italian character NER ([f16ca23](https://github.com/echoes-io/mcp-server/commit/f16ca2392b138ef023fc76c9c1d293db8de72b4c))
* implement index-rag tool for GraphRAG chapter indexing ([056cee1](https://github.com/echoes-io/mcp-server/commit/056cee146682942dff5b9bbf72b17568166726fe))
* implement index-tracker tool for filesystem to database sync ([ab821cf](https://github.com/echoes-io/mcp-server/commit/ab821cf0904c91f4df55ab0903ed7d1c8d1dd3c3))
* implement rag-search tool for semantic chapter search ([32e5727](https://github.com/echoes-io/mcp-server/commit/32e5727bd1c7bb6c064ea5c42420e8b447490849))


### BREAKING CHANGES

* Complete GraphRAG implementation with hybrid fallback system

Features:
- Add GraphRAG with semantic, character, temporal, and location edges
- Implement hybrid RAG system (GraphRAG primary + sqlite-vec fallback)
- Create ItalianCharacterNER with 90%+ accuracy for character detection
- Add database synchronization for timeline/arc/episode/chapter records
- Support BGE-Base-v1.5, E5-Small-v2, and Gemini embedding providers

Performance:
- Index 466 chapters in <1 second (558 chapters/second)
- Sub-second search queries on large datasets
- Memory efficient: <50MB for 466 chapters
- Graceful fallback system ensures 100% uptime

Testing:
- Add full-scale integration tests with real timeline data
- Comprehensive character extraction validation
- Performance benchmarks and memory usage analysis
- 9/9 integration tests passing

Technical Implementation:
- GraphRAG: 4 edge types (semantic, character, temporal, location)
- Character NER: 100+ Italian common words filtering
- Database sync: Auto-create timeline hierarchy
- Hybrid search: GraphRAG → vector fallback with timeout protection
- Content-aware embeddings for realistic similarity scoring

Closes: Phase 1 (consolidation), Phase 2 (GraphRAG), Phase 3 (character detection)
Progress: 85% roadmap complete, ready for Phase 4 (missing MCP tools)
* Complete restructure of src/ folder, removed all previous implementations

# [3.0.0](https://github.com/echoes-io/mcp-server/compare/v2.2.0...v3.0.0) (2025-12-18)


### Code Refactoring

* consolidate types, schemas and utils into src/ ([851400f](https://github.com/echoes-io/mcp-server/commit/851400fd400310e153a780e60e97d2dfef1c5d86))


### BREAKING CHANGES

* Remove dependencies on @echoes-io/models and @echoes-io/utils packages

# [2.2.0](https://github.com/echoes-io/mcp-server/compare/v2.1.0...v2.2.0) (2025-12-16)


### Features

* enhance semantic search with advanced embedding models ([1ebd969](https://github.com/echoes-io/mcp-server/commit/1ebd96947d9f5c61642fd32a1d98d11b65257dbc))

# [2.1.0](https://github.com/echoes-io/mcp-server/compare/v2.0.0...v2.1.0) (2025-12-16)


### Features

* enhance semantic search with advanced embedding models ([c822672](https://github.com/echoes-io/mcp-server/commit/c822672fac78cb2d290c476c318fe73d9f047a5a))

# [2.0.0](https://github.com/echoes-io/mcp-server/compare/v1.9.1...v2.0.0) (2025-12-16)


### Bug Fixes

* update RAG provider types to match @echoes-io/rag v1.3.1 ([b500adb](https://github.com/echoes-io/mcp-server/commit/b500adb59bb55540fd1babb1eb4c09f8fb3acd49))


### BREAKING CHANGES

* 'e5-large' provider no longer supported, use 'embeddinggemma' instead

## [1.9.1](https://github.com/echoes-io/mcp-server/compare/v1.9.0...v1.9.1) (2025-12-15)


### Performance Improvements

* :arrow_up: Upped `rag`, moving to `llamaindex` and `lancedb` ([fe919f7](https://github.com/echoes-io/mcp-server/commit/fe919f776862f8e0148b967e59d20a1ee88938ad))

# [1.9.0](https://github.com/echoes-io/mcp-server/compare/v1.8.2...v1.9.0) (2025-12-12)


### Features

* rename agent from 'default' to 'dev' and add code tool ([73abe4d](https://github.com/echoes-io/mcp-server/commit/73abe4de83b317cb0759aa9e91f587b13e522064))

## [1.8.2](https://github.com/echoes-io/mcp-server/compare/v1.8.1...v1.8.2) (2025-12-11)


### Performance Improvements

* :arrow_up: Upped `@echoes-io/utils` to better support word counting ([19f4e90](https://github.com/echoes-io/mcp-server/commit/19f4e90888deaf4d334d1c971d853bca65fda1c6))

## [1.8.1](https://github.com/echoes-io/mcp-server/compare/v1.8.0...v1.8.1) (2025-12-09)


### Bug Fixes

* :ambulance: Fixed a ricorsion ([6250563](https://github.com/echoes-io/mcp-server/commit/62505632c335d0b7530ce9827fbc1d54933bbc6c))

# [1.8.0](https://github.com/echoes-io/mcp-server/compare/v1.7.0...v1.8.0) (2025-12-06)


### Features

* **prompts:** implement MCP prompts system for timeline content creation ([deb9b85](https://github.com/echoes-io/mcp-server/commit/deb9b85216523a85ebe392514091a0b01eddb639))

# [1.7.0](https://github.com/echoes-io/mcp-server/compare/v1.6.0...v1.7.0) (2025-12-05)


### Features

* :sparkles: Added the ability to be multi timeline ([6902de1](https://github.com/echoes-io/mcp-server/commit/6902de15fe5b83db6fd0912a1288fe01f62167b5))


### Performance Improvements

* :arrow_up: Upped deps ([838557b](https://github.com/echoes-io/mcp-server/commit/838557b3205ec95351a8de878cfd48d7e6d9e61b))

# [1.6.0](https://github.com/echoes-io/mcp-server/compare/v1.5.0...v1.6.0) (2025-12-03)


### Features

* **kiro:** migrate from Amazon Q to Kiro agent configuration ([cb6860d](https://github.com/echoes-io/mcp-server/commit/cb6860d8aa1bbac138c1df7f20b68e4ca48e2145))

# [1.5.0](https://github.com/echoes-io/mcp-server/compare/v1.4.2...v1.5.0) (2025-11-03)


### Features

* :sparkles: Added the new version of rag to index characters ([bec4e90](https://github.com/echoes-io/mcp-server/commit/bec4e90ccd045d350c236b670743ae719ee64549))

## [1.4.2](https://github.com/echoes-io/mcp-server/compare/v1.4.1...v1.4.2) (2025-10-30)


### Bug Fixes

* :ambulance: Fixed string parsing and error display ([bbde118](https://github.com/echoes-io/mcp-server/commit/bbde1183b6cec0fc08e6a85342042db479da76b0))

## [1.4.1](https://github.com/echoes-io/mcp-server/compare/v1.4.0...v1.4.1) (2025-10-30)


### Performance Improvements

* :truck: Renamed raf_data to rag ([af367f5](https://github.com/echoes-io/mcp-server/commit/af367f5336c678c7670214cad2be4ecd728aa96d))

# [1.4.0](https://github.com/echoes-io/mcp-server/compare/v1.3.4...v1.4.0) (2025-10-30)


### Features

* :sparkles: Moving the `timeline` config from env var to param ([0abb622](https://github.com/echoes-io/mcp-server/commit/0abb62256a4f4136f4a1904eb870b10ffca4f955))

## [1.3.4](https://github.com/echoes-io/mcp-server/compare/v1.3.3...v1.3.4) (2025-10-29)


### Performance Improvements

* :truck: Moved `chapter.excerpt` to `chapter.summary` and `chapter.date` type from `Date` to `string` ([8c0a1c9](https://github.com/echoes-io/mcp-server/commit/8c0a1c9b2921513f38e2cd9a21f196f1a83ade67))

## [1.3.3](https://github.com/echoes-io/mcp-server/compare/v1.3.2...v1.3.3) (2025-10-29)


### Bug Fixes

* :bug: Fixing bad filename template and episode 0 ([42eded5](https://github.com/echoes-io/mcp-server/commit/42eded5cb0f4c4129e463bf5595af563aa6ebf53))

## [1.3.2](https://github.com/echoes-io/mcp-server/compare/v1.3.1...v1.3.2) (2025-10-28)


### Bug Fixes

* :bug: Fixed the rag indexing with multi-arc in mind ([f2f47c8](https://github.com/echoes-io/mcp-server/commit/f2f47c8da30ac1141601060373fc4ad2e1d62319))

## [1.3.1](https://github.com/echoes-io/mcp-server/compare/v1.3.0...v1.3.1) (2025-10-28)


### Bug Fixes

* :bug: Fixed a bug preventing to create chapters ([f782718](https://github.com/echoes-io/mcp-server/commit/f7827186b48a79dc21b8462cf2e24c3b5acd2c76))

# [1.3.0](https://github.com/echoes-io/mcp-server/compare/v1.2.0...v1.3.0) (2025-10-28)


### Features

* :sparkles: Added the `book-generate` tool ([2922659](https://github.com/echoes-io/mcp-server/commit/292265933dd9729a9dca37b16a684363207a92fd))


### Performance Improvements

* :sparkles: Using rag with sqlite ([cd4e746](https://github.com/echoes-io/mcp-server/commit/cd4e746cd265cc848a020f10f6466b16df8807ab))

# [1.2.0](https://github.com/echoes-io/mcp-server/compare/v1.1.0...v1.2.0) (2025-10-27)


### Features

* :sparkles: Added the rag system ([04e8956](https://github.com/echoes-io/mcp-server/commit/04e895643b0f5dd18a611a7bf49e9383a2fb6780))

# [1.1.0](https://github.com/echoes-io/mcp-server/compare/v1.0.0...v1.1.0) (2025-10-24)


### Features

* :sparkles: Added `chapter-delete` and auto delete during sync ([b036211](https://github.com/echoes-io/mcp-server/commit/b03621166e30c1004d29e9267ecada70862974a3))
* :sparkles: Added the `chapter-info`, `episode-info`, `words-count` and `timeline-sync` tools ([5212852](https://github.com/echoes-io/mcp-server/commit/521285285103b3e432e329c34bee2fdd02d06abd))
* :sparkles: Added the `chapter-refresh` tool ([0c632ee](https://github.com/echoes-io/mcp-server/commit/0c632ee601683f5b9c7ffd8c567c1a9dfb8d641b))
* :sparkles: Added the `stats` tool ([82afd12](https://github.com/echoes-io/mcp-server/commit/82afd126117ad8932b7026258d5ac0f0d682d386))
* add episode-update tool and enhance chapter-delete ([b4ccad1](https://github.com/echoes-io/mcp-server/commit/b4ccad1d2939d985bc398980d7814f710f74c745))


### Performance Improvements

* :zap: Using timeline as env var ([2097684](https://github.com/echoes-io/mcp-server/commit/20976847a9998c76efe522c4ae568caf26c49372))

# 1.0.0 (2025-10-23)


### Features

* :sparkles: First empty implementation of the mcp server ([d098da2](https://github.com/echoes-io/mcp-server/commit/d098da2f1910f7673f45e212e18707cb1cca6ac1))

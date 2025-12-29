"""MCP Server for Echoes."""

import asyncio
import json
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import GetPromptResult, Prompt, PromptArgument, PromptMessage, TextContent, Tool

from . import __version__
from .database import Database
from .indexer import embed_query
from .prompts import get_prompt, list_prompts
from .tools import (
    index_timeline,
    search_entities,
    search_relations,
    search_semantic,
    stats,
    words_count,
)

# Setup logging to stderr (stdout is used for MCP JSON-RPC)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("echoes-mcp")

# Initialize server
server = Server("echoes-mcp-server")

# Database path from cwd
DB_PATH = Path.cwd() / "db"
CONTENT_PATH = Path.cwd() / "content"
TIMELINE = Path.cwd().name  # Use directory name as timeline name
logger.info(f"Server starting, cwd={Path.cwd()}, db_path={DB_PATH}, timeline={TIMELINE}")


def get_db() -> Database:
    """Get database connection."""
    return Database(DB_PATH)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="version",
            description="Get the current version of echoes-mcp-server",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="words-count",
            description="Count words and statistics in a markdown file. IMPORTANT: Use absolute paths only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Absolute path to markdown file"},
                },
                "required": ["file"],
            },
        ),
        Tool(
            name="stats",
            description="Get aggregate statistics from the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "arc": {"type": "string", "description": "Filter by arc"},
                    "episode": {"type": "integer", "description": "Filter by episode"},
                    "pov": {"type": "string", "description": "Filter by POV character"},
                },
            },
        ),
        Tool(
            name="index",
            description="Index timeline content into LanceDB. IMPORTANT: Use absolute paths only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_path": {
                        "type": "string",
                        "description": "Absolute path to content directory",
                    },
                    "force": {"type": "boolean", "description": "Force full re-index"},
                    "arc": {"type": "string", "description": "Index only this arc"},
                    "extract_entities": {
                        "type": "boolean",
                        "description": "Extract entities/relations (slower but richer data)",
                        "default": True,
                    },
                },
                "required": ["content_path"],
            },
        ),
        Tool(
            name="search-semantic",
            description="Semantic search on chapters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "arc": {"type": "string", "description": "Filter by arc"},
                    "episode": {"type": "integer", "description": "Filter by episode"},
                    "pov": {"type": "string", "description": "Filter by POV"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search-entities",
            description="Search entities (characters, locations, events)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "name": {"type": "string", "description": "Exact name match"},
                    "type": {
                        "type": "string",
                        "description": "Entity type",
                        "enum": ["CHARACTER", "LOCATION", "EVENT", "OBJECT", "EMOTION"],
                    },
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
            },
        ),
        Tool(
            name="search-relations",
            description="Search relations between entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity": {"type": "string", "description": "Find relations of this entity"},
                    "source": {"type": "string", "description": "Source entity"},
                    "target": {"type": "string", "description": "Target entity"},
                    "type": {"type": "string", "description": "Relation type"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
            },
        ),
    ]


def _require_absolute_path(path: str, param_name: str) -> Path:
    """Validate that path is absolute and return as Path object."""
    p = Path(path)
    if not p.is_absolute():
        raise ValueError(f"{param_name} must be an absolute path, got: {path}")
    return p


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool call: {name} with args: {arguments}")
    try:
        match name:
            case "version":
                result = {"version": __version__, "package": "echoes-mcp-server"}
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            case "words-count":
                file_path = _require_absolute_path(arguments["file"], "file")
                result = words_count(str(file_path))
                logger.debug(f"words-count result: {result}")
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            case "stats":
                db = get_db()
                result = await stats(
                    db,
                    arc=arguments.get("arc"),
                    episode=arguments.get("episode"),
                    pov=arguments.get("pov"),
                )
                logger.debug(f"stats result: chapters={result['chapters']}")
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            case "index":
                content_path = _require_absolute_path(arguments["content_path"], "content_path")
                logger.info(f"Starting index: content_path={content_path}")
                try:
                    result = await index_timeline(
                        content_path,
                        DB_PATH,
                        force=arguments.get("force", False),
                        arc_filter=arguments.get("arc"),
                        quiet=True,  # Suppress console output for MCP
                        extract_entities=arguments.get("extract_entities", True),
                    )
                    logger.info(f"Index complete: {result}")
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                except Exception as e:
                    error_msg = f"Indexing failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return [TextContent(type="text", text=f"ERROR: {error_msg}")]

            case "search-semantic":
                db = get_db()
                logger.debug(f"Embedding query: {arguments['query']}")
                query_vector = embed_query(arguments["query"])
                results = await search_semantic(
                    db,
                    query_vector,
                    arc=arguments.get("arc"),
                    episode=arguments.get("episode"),
                    pov=arguments.get("pov"),
                    limit=arguments.get("limit", 10),
                )
                logger.debug(f"search-semantic found {len(results)} results")
                return [TextContent(type="text", text=json.dumps(results, indent=2))]

            case "search-entities":
                db = get_db()
                query_vector = None
                if arguments.get("query"):
                    query_vector = embed_query(arguments["query"])
                results = await search_entities(
                    db,
                    query_vector=query_vector,
                    arc=arguments.get("arc"),
                    name=arguments.get("name"),
                    entity_type=arguments.get("type"),
                    limit=arguments.get("limit", 10),
                )
                logger.debug(f"search-entities found {len(results)} results")
                return [TextContent(type="text", text=json.dumps(results, indent=2))]

            case "search-relations":
                db = get_db()
                results = await search_relations(
                    db,
                    arc=arguments.get("arc"),
                    entity=arguments.get("entity"),
                    source=arguments.get("source"),
                    target=arguments.get("target"),
                    relation_type=arguments.get("type"),
                    limit=arguments.get("limit", 10),
                )
                logger.debug(f"search-relations found {len(results)} results")
                return [TextContent(type="text", text=json.dumps(results, indent=2))]

            case _:
                logger.warning(f"Unknown tool: {name}")
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {e}")]


async def run_server() -> None:
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """List available prompts."""
    prompts_data = list_prompts()
    return [
        Prompt(
            name=p["name"],
            description=p["description"],
            arguments=[
                PromptArgument(
                    name=arg["name"],
                    description=arg["description"],
                    required=arg["required"],
                )
                for arg in p["arguments"]
            ],
        )
        for p in prompts_data["prompts"]
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """Get a prompt by name with substituted placeholders."""
    logger.info(f"Get prompt: {name} with args: {arguments}")
    result = get_prompt(
        name=name,
        args=arguments or {},
        timeline=TIMELINE,
        content_path=CONTENT_PATH,
    )
    return GetPromptResult(
        messages=[
            PromptMessage(
                role=msg["role"],
                content=TextContent(type="text", text=msg["content"]["text"]),
            )
            for msg in result["messages"]
        ]
    )


def main() -> None:
    """Run the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()

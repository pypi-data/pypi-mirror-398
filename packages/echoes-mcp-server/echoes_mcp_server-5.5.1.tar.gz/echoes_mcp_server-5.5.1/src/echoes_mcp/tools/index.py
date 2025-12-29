"""Index tool - index timeline content into LanceDB."""

import logging
import time
from pathlib import Path
from typing import TypedDict

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from ..database import Database
from ..indexer.embeddings import embed_texts
from ..indexer.extractor import (
    ENTITY_TYPE_MAP,
    RELATION_TYPE_MAP,
    extract_entities_and_relations,
)
from ..indexer.scanner import ChapterFile, scan_content
from .words_count import count_paragraphs, count_words, strip_markdown

logger = logging.getLogger(__name__)


class IndexResult(TypedDict):
    """Result of index operation."""

    indexed: int
    updated: int
    deleted: int
    entities: int
    relations: int
    duration_seconds: float


def prepare_chapter_record(
    chapter: ChapterFile,
    vector: list[float],
) -> dict:
    """Prepare chapter record for LanceDB."""
    # Clean content for stats
    clean_content = strip_markdown(chapter["content"])

    return {
        "id": f"{chapter['arc']}:ep{chapter['episode']:02d}:ch{chapter['chapter']:03d}",
        "file_path": chapter["file_path"],
        "file_hash": chapter["file_hash"],
        "arc": chapter["arc"],
        "episode": chapter["episode"],
        "chapter": chapter["chapter"],
        "pov": chapter["pov"],
        "title": chapter["title"],
        "location": chapter["location"],
        "date": chapter["date"],
        "content": chapter["content"],
        "summary": chapter["summary"] or chapter["content"][:200],
        "word_count": count_words(clean_content),
        "char_count": len(clean_content),
        "paragraph_count": count_paragraphs(clean_content),
        "vector": vector,
        "entities": [],  # Will be populated by entity extraction
        "indexed_at": int(time.time()),
    }


async def index_timeline(
    content_path: str | Path,
    db_path: str | Path = ".lancedb",
    force: bool = False,
    arc_filter: str | None = None,
    quiet: bool = False,
    extract_entities: bool = True,
) -> IndexResult:
    """
    Index timeline content into LanceDB.

    Args:
        content_path: Path to content directory
        db_path: Path to LanceDB database
        force: Force full re-index (ignore hashes)
        arc_filter: Only index this arc
        quiet: Suppress console output (for MCP server)
        extract_entities: Whether to extract entities/relations (slower but richer)
    """
    from .. import __version__

    start_time = time.time()
    content_path = Path(content_path)
    db = Database(db_path)

    # Console output only if not quiet
    console = Console(quiet=quiet)

    # Check if version changed - auto-force reindex
    indexed_version = db.get_indexed_version()
    if indexed_version and indexed_version != __version__ and not force:
        console.print(
            f"[yellow]Version changed ({indexed_version} → {__version__}), forcing re-index[/yellow]"
        )
        force = True

    # Scan filesystem
    console.print("[dim]Scanning files...[/dim]")
    chapters = scan_content(content_path)

    if arc_filter:
        chapters = [c for c in chapters if c["arc"] == arc_filter]

    console.print(f"[green]Found {len(chapters)} chapters[/green]")

    if not chapters:
        return IndexResult(
            indexed=0,
            updated=0,
            deleted=0,
            entities=0,
            relations=0,
            duration_seconds=time.time() - start_time,
        )

    # Get existing hashes for incremental indexing
    existing_hashes = {} if force else db.get_chapter_hashes()

    # Filter to only changed chapters
    to_index: list[ChapterFile] = []
    for chapter in chapters:
        existing_hash = existing_hashes.get(chapter["file_path"])
        if existing_hash != chapter["file_hash"]:
            to_index.append(chapter)

    # Find deleted chapters
    current_paths = {c["file_path"] for c in chapters}
    deleted_paths = [p for p in existing_hashes if p not in current_paths]

    if not to_index and not deleted_paths:
        console.print("[yellow]No changes detected[/yellow]")
        return IndexResult(
            indexed=0,
            updated=0,
            deleted=0,
            entities=0,
            relations=0,
            duration_seconds=time.time() - start_time,
        )

    console.print(f"[blue]Indexing {len(to_index)} chapters...[/blue]")

    # Generate embeddings for chapters to index
    records = []
    if to_index:
        texts = [c["content"][:2000] for c in to_index]

        if quiet:
            # No progress bar for MCP server
            vectors = embed_texts(texts)
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("ETA:"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Embedding", total=len(texts))

                def update_progress(completed: int, _total: int) -> None:
                    progress.update(task, completed=completed)

                vectors = embed_texts(texts, progress_callback=update_progress)

        # Prepare records
        for chapter, vector in zip(to_index, vectors, strict=True):
            records.append(prepare_chapter_record(chapter, vector))

    # Extract entities if enabled
    total_entities = 0
    total_relations = 0
    entity_records: list[dict] = []
    relation_records: list[dict] = []
    entity_chapters: dict[str, list[str]] = {}  # entity_id -> chapter_ids

    if extract_entities and records:
        console.print("[blue]Extracting entities...[/blue]")
        now = int(time.time())

        for record in records:
            try:
                result = extract_entities_and_relations(record["content"])
                arc = record["arc"]
                chapter_id = record["id"]

                # Process entities - build lookup for relation types
                chapter_entity_ids = []
                entity_type_lookup: dict[str, str] = {}  # name -> type
                for e in result["entities"]:
                    entity_type = ENTITY_TYPE_MAP.get(e["type"], e["type"])
                    entity_id = f"{arc}:{entity_type}:{e['name']}"
                    chapter_entity_ids.append(entity_id)
                    entity_type_lookup[e["name"]] = entity_type

                    # Track which chapters mention this entity
                    if entity_id not in entity_chapters:
                        entity_chapters[entity_id] = []
                        # First time seeing this entity, create record
                        entity_records.append(
                            {
                                "id": entity_id,
                                "arc": arc,
                                "name": e["name"],
                                "type": entity_type,
                                "description": e.get("description", ""),
                                "aliases": [],
                                "vector": [0.0] * 768,  # Placeholder, will embed later
                                "chapters": [],  # Will populate after
                                "chapter_count": 0,
                                "first_appearance": chapter_id,
                                "indexed_at": now,
                            }
                        )
                    entity_chapters[entity_id].append(chapter_id)

                record["entities"] = chapter_entity_ids
                total_entities += len(result["entities"])

                # Process relations
                for r in result["relations"]:
                    rel_type = RELATION_TYPE_MAP.get(r["type"], r["type"])
                    source_type = entity_type_lookup.get(r["source"], "CHARACTER")
                    target_type = entity_type_lookup.get(r["target"], "CHARACTER")
                    source_id = f"{arc}:{source_type}:{r['source']}"
                    target_id = f"{arc}:{target_type}:{r['target']}"
                    rel_id = f"{arc}:{r['source']}:{rel_type}:{r['target']}"

                    relation_records.append(
                        {
                            "id": rel_id,
                            "arc": arc,
                            "source_entity": source_id,
                            "target_entity": target_id,
                            "type": rel_type,
                            "description": "",
                            "weight": 1.0,
                            "chapters": [chapter_id],
                            "indexed_at": now,
                        }
                    )
                total_relations += len(result["relations"])

                logger.debug(
                    f"Chapter {chapter_id}: {len(result['entities'])} entities, {len(result['relations'])} relations"
                )
            except Exception as e:
                logger.warning(f"Entity extraction failed for {record['id']}: {e}")
                record["entities"] = []

        # Update entity chapter lists
        for er in entity_records:
            er["chapters"] = entity_chapters.get(er["id"], [])
            er["chapter_count"] = len(er["chapters"])

    # Count new vs updated
    indexed = sum(1 for r in records if r["file_path"] not in existing_hashes)
    updated = len(records) - indexed

    # Save to database
    if records:
        console.print("[dim]Saving to database...[/dim]")
        db.upsert_chapters(records)

    if entity_records:
        console.print(f"[dim]Saving {len(entity_records)} entities...[/dim]")
        db.upsert_entities(entity_records)

    if relation_records:
        console.print(f"[dim]Saving {len(relation_records)} relations...[/dim]")
        db.upsert_relations(relation_records)

    # Delete removed chapters
    deleted = 0
    if deleted_paths:
        deleted = db.delete_chapters_by_paths(deleted_paths)

    # Save version after successful indexing
    if records or deleted_paths:
        db.set_indexed_version(__version__)

    return IndexResult(
        indexed=indexed,
        updated=updated,
        deleted=deleted,
        entities=total_entities,
        relations=total_relations,
        duration_seconds=round(time.time() - start_time, 2),
    )

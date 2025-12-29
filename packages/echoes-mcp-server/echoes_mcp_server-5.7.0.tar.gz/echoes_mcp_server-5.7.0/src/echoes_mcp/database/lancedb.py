"""LanceDB database connection and operations."""

import contextlib
import json
from pathlib import Path
from typing import Any

import lancedb
from lancedb.table import Table

from .. import __version__
from .schemas import ChapterRecord, EntityRecord, RelationRecord

CHAPTERS_TABLE = "chapters"
ENTITIES_TABLE = "entities"
RELATIONS_TABLE = "relations"
METADATA_FILE = "metadata.json"


class Database:
    """LanceDB database wrapper for Echoes."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._db: lancedb.DBConnection | None = None
        self._check_migration()

    def _check_migration(self) -> None:
        """Check if database needs migration and handle it."""
        metadata_path = self.db_path / METADATA_FILE

        if not metadata_path.exists():
            # New database, create metadata
            self._save_metadata()
            return

        try:
            with metadata_path.open() as f:
                metadata = json.load(f)

            db_version = metadata.get("version", "0.0.0")
            if db_version != __version__:
                print(f"🔄 Database version mismatch: {db_version} → {__version__}")
                print("🗑️  Removing old database for schema migration...")

                # Remove all tables but keep directory
                for table_name in [CHAPTERS_TABLE, ENTITIES_TABLE, RELATIONS_TABLE]:
                    table_path = self.db_path / f"{table_name}.lance"
                    if table_path.exists():
                        import shutil

                        shutil.rmtree(table_path)

                self._save_metadata()
                print("✅ Database ready for re-indexing")

        except (json.JSONDecodeError, KeyError):
            # Corrupted metadata, force recreation
            self._save_metadata()

    def _save_metadata(self) -> None:
        """Save current version to metadata file."""
        self.db_path.mkdir(exist_ok=True)
        metadata = {"version": __version__}
        with (self.db_path / METADATA_FILE).open("w") as f:
            json.dump(metadata, f)

    @property
    def db(self) -> lancedb.DBConnection:
        """Lazy connection to LanceDB."""
        if self._db is None:
            self._db = lancedb.connect(self.db_path)
        return self._db

    def _get_or_create_table(self, name: str, schema: type) -> Table:
        """Get existing table or create new one with schema."""
        existing = self.db.list_tables().tables
        if name in existing:
            return self.db.open_table(name)
        return self.db.create_table(name, schema=schema)

    @property
    def chapters(self) -> Table:
        """Chapters table."""
        return self._get_or_create_table(CHAPTERS_TABLE, ChapterRecord)

    @property
    def entities(self) -> Table:
        """Entities table."""
        return self._get_or_create_table(ENTITIES_TABLE, EntityRecord)

    @property
    def relations(self) -> Table:
        """Relations table."""
        return self._get_or_create_table(RELATIONS_TABLE, RelationRecord)

    def upsert_chapters(self, records: list[dict[str, Any]]) -> int:
        """Insert or update chapters. Returns count."""
        if not records:
            return 0
        ids = [r["id"] for r in records]
        with contextlib.suppress(Exception):
            self.chapters.delete(f"id IN {tuple(ids)}" if len(ids) > 1 else f"id = '{ids[0]}'")
        self.chapters.add(records)
        return len(records)

    def upsert_entities(self, records: list[dict[str, Any]]) -> int:
        """Insert or update entities. Returns count."""
        if not records:
            return 0
        ids = [r["id"] for r in records]
        with contextlib.suppress(Exception):
            self.entities.delete(f"id IN {tuple(ids)}" if len(ids) > 1 else f"id = '{ids[0]}'")
        self.entities.add(records)
        return len(records)

    def upsert_relations(self, records: list[dict[str, Any]]) -> int:
        """Insert or update relations. Returns count."""
        if not records:
            return 0
        ids = [r["id"] for r in records]
        with contextlib.suppress(Exception):
            self.relations.delete(f"id IN {tuple(ids)}" if len(ids) > 1 else f"id = '{ids[0]}'")
        self.relations.add(records)
        return len(records)

    def get_chapter_hashes(self) -> dict[str, str]:
        """Get all chapter file_path -> file_hash mappings."""
        try:
            results = (
                self.chapters.search().select(["file_path", "file_hash"]).limit(10000).to_list()
            )
            return {r["file_path"]: r["file_hash"] for r in results}
        except Exception:
            return {}

    def delete_chapters_by_paths(self, paths: list[str]) -> int:
        """Delete chapters by file paths. Returns count."""
        if not paths:
            return 0
        try:
            filter_expr = (
                f"file_path IN {tuple(paths)}" if len(paths) > 1 else f"file_path = '{paths[0]}'"
            )
            self.chapters.delete(filter_expr)
            return len(paths)
        except Exception:
            return 0

    def close(self) -> None:
        """Close database connection."""
        self._db = None

    def get_indexed_version(self) -> str | None:
        """Get the version used for last indexing."""
        metadata_path = self.db_path / METADATA_FILE
        if not metadata_path.exists():
            return None
        try:
            data = json.loads(metadata_path.read_text())
            return data.get("indexed_version")
        except Exception:
            return None

    def set_indexed_version(self, version: str) -> None:
        """Set the version used for indexing."""
        metadata_path = self.db_path / METADATA_FILE
        self.db_path.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps({"indexed_version": version}))

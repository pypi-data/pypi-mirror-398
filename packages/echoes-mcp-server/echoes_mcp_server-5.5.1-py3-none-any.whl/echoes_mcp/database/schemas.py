"""Pydantic schemas for LanceDB tables."""

from typing import Literal

from lancedb.pydantic import LanceModel, Vector
from pydantic import Field

EntityType = Literal["CHARACTER", "LOCATION", "EVENT", "OBJECT", "EMOTION"]

RelationType = Literal[
    # Character relations
    "LOVES",
    "HATES",
    "KNOWS",
    "RELATED_TO",
    "FRIENDS_WITH",
    "ENEMIES_WITH",
    # Spatial relations
    "LOCATED_IN",
    "LIVES_IN",
    "TRAVELS_TO",
    # Temporal relations
    "HAPPENS_BEFORE",
    "HAPPENS_AFTER",
    "CAUSES",
    # Object relations
    "OWNS",
    "USES",
    "SEEKS",
]

# Default embedding dimension (sentence-transformers paraphrase-multilingual)
EMBEDDING_DIM = 768


class ChapterRecord(LanceModel):
    """Schema for chapters.lance table."""

    # Identification
    id: str = Field(description="Unique ID: arc:episode:chapter")
    file_path: str = Field(description="Relative path to markdown file")
    file_hash: str = Field(description="SHA256 hash for change detection")

    # Hierarchy
    arc: str
    episode: int
    chapter: int

    # Metadata from frontmatter
    pov: str = Field(description="Point of view character")
    title: str
    location: str | None = None
    date: str | None = Field(default=None, description="Narrative date")

    # Content
    content: str = Field(description="Clean text without frontmatter/markdown")
    summary: str | None = Field(default=None, description="Short summary")

    # Statistics
    word_count: int
    char_count: int
    paragraph_count: int

    # RAG
    vector: Vector(EMBEDDING_DIM)  # type: ignore[valid-type]
    entities: list[str] = Field(default_factory=list, description="Entity IDs")

    # Metadata
    indexed_at: int = Field(description="Unix timestamp")


class EntityRecord(LanceModel):
    """Schema for entities.lance table."""

    id: str = Field(description="Unique ID: arc:type:name")
    arc: str = Field(description="Arc this entity belongs to")
    name: str
    type: str  # EntityType as string for LanceDB compatibility
    description: str
    aliases: list[str] = Field(default_factory=list)

    # RAG
    vector: Vector(EMBEDDING_DIM)  # type: ignore[valid-type]

    # References
    chapters: list[str] = Field(default_factory=list, description="Chapter IDs")
    chapter_count: int = 0
    first_appearance: str | None = None

    # Metadata
    indexed_at: int


class RelationRecord(LanceModel):
    """Schema for relations.lance table."""

    id: str = Field(description="Unique ID: arc:source:type:target")
    arc: str = Field(description="Arc this relation belongs to")
    source_entity: str = Field(description="Source entity ID")
    target_entity: str = Field(description="Target entity ID")
    type: str = Field(description="Relation type")
    description: str
    weight: float = Field(ge=0.0, le=1.0, description="Importance/frequency")

    # References
    chapters: list[str] = Field(default_factory=list)

    # Metadata
    indexed_at: int

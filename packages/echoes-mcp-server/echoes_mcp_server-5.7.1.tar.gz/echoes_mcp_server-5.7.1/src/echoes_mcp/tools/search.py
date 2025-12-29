"""Search tools - semantic search on chapters, entities, relations."""

from typing import Any, TypedDict

from ..database import Database


class SearchResult(TypedDict):
    """Single search result."""

    id: str
    title: str
    pov: str
    arc: str
    episode: int
    chapter: int
    score: float
    summary: str


class EntitySearchResult(TypedDict):
    """Entity search result."""

    id: str
    name: str
    type: str
    description: str
    aliases: list[str]
    chapter_count: int
    score: float


class RelationSearchResult(TypedDict):
    """Relation search result."""

    id: str
    source: dict[str, str]
    target: dict[str, str]
    type: str
    description: str
    weight: float
    chapter_count: int


async def search_semantic(
    db: Database,
    query_vector: list[float],
    arc: str | None = None,
    episode: int | None = None,
    pov: str | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    """
    Semantic search on chapters.

    Args:
        db: Database connection
        query_vector: Pre-computed query embedding
        arc: Filter by arc
        episode: Filter by episode
        pov: Filter by POV
        limit: Max results
    """
    # Build filter
    filters: list[str] = []
    if arc:
        filters.append(f"arc = '{arc}'")
    if episode is not None:
        filters.append(f"episode = {episode}")
    if pov:
        filters.append(f"pov = '{pov}'")

    filter_expr = " AND ".join(filters) if filters else None

    # Vector search
    search = db.chapters.search(query_vector).limit(limit)
    if filter_expr:
        search = search.where(filter_expr)

    results: list[dict[str, Any]] = search.to_list()

    return [
        SearchResult(
            id=r["id"],
            title=r["title"],
            pov=r["pov"],
            arc=r["arc"],
            episode=r["episode"],
            chapter=r["chapter"],
            score=float(r.get("_distance", 0)),
            summary=r.get("content", "")[:200] + "..." if r.get("content") else "",
        )
        for r in results
    ]


async def search_entities(
    db: Database,
    query_vector: list[float] | None = None,
    arc: str | None = None,
    name: str | None = None,
    entity_type: str | None = None,
    limit: int = 10,
) -> list[EntitySearchResult]:
    """
    Search entities by name or semantic similarity.

    Args:
        db: Database connection
        query_vector: Query embedding for semantic search
        arc: Filter by arc (recommended to avoid cross-arc contamination)
        name: Exact name match
        entity_type: Filter by type (CHARACTER, LOCATION, etc.)
        limit: Max results
    """
    filters: list[str] = []
    if arc:
        filters.append(f"arc = '{arc}'")
    if name:
        filters.append(f"name = '{name}'")
    if entity_type:
        filters.append(f"type = '{entity_type}'")

    filter_expr = " AND ".join(filters) if filters else None

    if query_vector:
        search = db.entities.search(query_vector).limit(limit)
    else:
        search = db.entities.search().limit(limit)

    if filter_expr:
        search = search.where(filter_expr)

    results: list[dict[str, Any]] = search.to_list()

    return [
        EntitySearchResult(
            id=r["id"],
            name=r["name"],
            type=r["type"],
            description=r["description"],
            aliases=r.get("aliases", []),
            chapter_count=r.get("chapter_count", 0),
            score=float(r.get("_distance", 0)),
        )
        for r in results
    ]


async def search_relations(
    db: Database,
    arc: str | None = None,
    entity: str | None = None,
    source: str | None = None,
    target: str | None = None,
    relation_type: str | None = None,
    limit: int = 10,
) -> list[RelationSearchResult]:
    """
    Search relations between entities.

    Args:
        db: Database connection
        arc: Filter by arc (recommended to avoid cross-arc contamination)
        entity: Find all relations involving this entity
        source: Filter by source entity
        target: Filter by target entity
        relation_type: Filter by relation type
        limit: Max results
    """
    filters: list[str] = []
    if arc:
        filters.append(f"arc = '{arc}'")
    if entity:
        filters.append(f"(source_entity = '{entity}' OR target_entity = '{entity}')")
    if source:
        filters.append(f"source_entity = '{source}'")
    if target:
        filters.append(f"target_entity = '{target}'")
    if relation_type:
        filters.append(f"type = '{relation_type}'")

    filter_expr = " AND ".join(filters) if filters else None

    search = db.relations.search().limit(limit)
    if filter_expr:
        search = search.where(filter_expr)

    results: list[dict[str, Any]] = search.to_list()

    # Enrich with entity info
    enriched: list[RelationSearchResult] = []
    for r in results:
        enriched.append(
            RelationSearchResult(
                id=r["id"],
                source={"id": r["source_entity"], "name": r["source_entity"].split(":")[-1]},
                target={"id": r["target_entity"], "name": r["target_entity"].split(":")[-1]},
                type=r["type"],
                description=r["description"],
                weight=r.get("weight", 0.0),
                chapter_count=len(r.get("chapters", [])),
            )
        )

    return enriched

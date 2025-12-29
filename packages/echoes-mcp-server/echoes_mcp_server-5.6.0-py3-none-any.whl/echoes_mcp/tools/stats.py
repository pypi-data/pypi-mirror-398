"""Stats tool - aggregate statistics from LanceDB."""

from typing import Any, TypedDict

from ..database import Database


class StatsResult(TypedDict):
    """Result of stats operation."""

    chapters: int
    words: int
    avg_words_per_chapter: float
    min_words: int
    max_words: int
    unique_povs: int
    pov_distribution: dict[str, int]
    arcs: list[str]
    episodes: int
    entities: dict[str, int]
    relations: int


async def stats(
    db: Database,
    arc: str | None = None,
    episode: int | None = None,
    pov: str | None = None,
) -> StatsResult:
    """
    Get aggregate statistics from the database.

    Args:
        db: Database connection
        arc: Filter by arc name
        episode: Filter by episode number
        pov: Filter by POV character
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

    # Query chapters
    query = db.chapters.search()
    if filter_expr:
        query = query.where(filter_expr)

    chapters: list[dict[str, Any]] = (
        query.select(["word_count", "pov", "arc", "episode"]).limit(10000).to_list()
    )

    if not chapters:
        return StatsResult(
            chapters=0,
            words=0,
            avg_words_per_chapter=0.0,
            min_words=0,
            max_words=0,
            unique_povs=0,
            pov_distribution={},
            arcs=[],
            episodes=0,
            entities={"total": 0, "characters": 0, "locations": 0, "events": 0},
            relations=0,
        )

    # Calculate chapter stats
    word_counts = [c["word_count"] for c in chapters]
    total_words = sum(word_counts)

    # POV distribution
    pov_dist: dict[str, int] = {}
    for c in chapters:
        pov_name = c["pov"]
        pov_dist[pov_name] = pov_dist.get(pov_name, 0) + 1

    # Arcs and episodes
    arcs = sorted({c["arc"] for c in chapters})
    episode_keys = {(c["arc"], c["episode"]) for c in chapters}

    # Entity stats
    entities = db.entities.search().select(["type"]).limit(10000).to_list()
    entity_counts = {"total": len(entities), "characters": 0, "locations": 0, "events": 0}
    for e in entities:
        etype = e["type"].lower() + "s"
        if etype in entity_counts:
            entity_counts[etype] += 1

    # Relation count
    relations = db.relations.search().limit(10000).to_list()

    return StatsResult(
        chapters=len(chapters),
        words=total_words,
        avg_words_per_chapter=round(total_words / len(chapters), 1) if chapters else 0.0,
        min_words=min(word_counts) if word_counts else 0,
        max_words=max(word_counts) if word_counts else 0,
        unique_povs=len(pov_dist),
        pov_distribution=pov_dist,
        arcs=arcs,
        episodes=len(episode_keys),
        entities=entity_counts,
        relations=len(relations),
    )

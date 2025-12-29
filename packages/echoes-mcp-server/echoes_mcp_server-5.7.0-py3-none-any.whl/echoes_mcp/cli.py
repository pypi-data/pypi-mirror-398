"""CLI interface for Echoes MCP Server."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from .database import Database
from .tools import index_timeline, stats, words_count

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """Echoes MCP Server - Narrative Knowledge Graph for storytelling."""
    pass


@cli.command("words-count")
@click.argument("file_path", type=click.Path(exists=True))
def words_count_cmd(file_path: str) -> None:
    """Count words and statistics in a markdown file."""
    try:
        result = words_count(file_path)
        console.print(f"[bold]Words:[/bold] {result['words']}")
        console.print(f"[bold]Characters:[/bold] {result['characters']}")
        console.print(f"[bold]Paragraphs:[/bold] {result['paragraphs']}")
        console.print(f"[bold]Reading time:[/bold] {result['reading_time_minutes']} min")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from e


@cli.command("stats")
@click.option("--db", "db_path", default="db", help="Path to LanceDB database")
@click.option("--arc", help="Filter by arc")
@click.option("--episode", type=int, help="Filter by episode")
@click.option("--pov", help="Filter by POV character")
def stats_cmd(db_path: str, arc: str | None, episode: int | None, pov: str | None) -> None:
    """Get aggregate statistics from the database."""
    db = Database(db_path)

    try:
        result = asyncio.run(stats(db, arc=arc, episode=episode, pov=pov))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from e

    # Summary
    console.print(f"\n[bold]Chapters:[/bold] {result['chapters']}")
    console.print(f"[bold]Total words:[/bold] {result['words']:,}")
    console.print(f"[bold]Avg words/chapter:[/bold] {result['avg_words_per_chapter']}")
    console.print(f"[bold]Range:[/bold] {result['min_words']} - {result['max_words']}")

    # POV distribution
    if result["pov_distribution"]:
        console.print("\n[bold]POV Distribution:[/bold]")
        table = Table()
        table.add_column("POV")
        table.add_column("Chapters", justify="right")
        for pov_name, count in sorted(result["pov_distribution"].items(), key=lambda x: -x[1]):
            table.add_row(pov_name, str(count))
        console.print(table)

    # Entities
    console.print(f"\n[bold]Entities:[/bold] {result['entities']['total']}")
    console.print(f"  Characters: {result['entities']['characters']}")
    console.print(f"  Locations: {result['entities']['locations']}")
    console.print(f"  Events: {result['entities']['events']}")
    console.print(f"[bold]Relations:[/bold] {result['relations']}")


@cli.command("index")
@click.argument("content_path", type=click.Path(exists=True))
@click.option("--db", "db_path", default="db", help="Path to LanceDB database")
@click.option("--force", is_flag=True, help="Force full re-index")
@click.option("--arc", help="Index only this arc")
def index_cmd(content_path: str, db_path: str, force: bool, arc: str | None) -> None:
    """Index timeline content into LanceDB."""
    from ..indexer.spacy_utils import SPACY_MODEL, SPACY_MODEL_URL, check_spacy_model

    # Check spaCy model availability early
    if not check_spacy_model():
        console.print(f"[red]❌ spaCy model '{SPACY_MODEL}' not found![/red]")
        console.print("[yellow]Please install it manually:[/yellow]")
        console.print(f"   pip install {SPACY_MODEL_URL}")
        raise click.Abort()

    result = asyncio.run(index_timeline(content_path, db_path, force=force, arc_filter=arc))

    console.print("\n[bold green]✓ Indexing complete![/bold green]")
    console.print(f"  New: {result['indexed']}")
    console.print(f"  Updated: {result['updated']}")
    console.print(f"  Deleted: {result['deleted']}")
    console.print(f"  Duration: {result['duration_seconds']:.1f}s")

    # Show summary stats if we indexed something
    if result["indexed"] > 0 or result["updated"] > 0:
        db = Database(db_path)
        try:
            summary = asyncio.run(stats(db, arc=arc))
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  📖 {summary['chapters']} chapters")
            console.print(f"  📝 {summary['words']:,} words")

            # Reading time (avg 200 words/min)
            reading_mins = summary["words"] // 200
            if reading_mins >= 60:
                hours = reading_mins // 60
                mins = reading_mins % 60
                console.print(f"  ⏱️  ~{hours}h {mins}m reading time")
            else:
                console.print(f"  ⏱️  ~{reading_mins}m reading time")

            # Arcs and episodes
            if summary.get("arcs"):
                console.print(f"  📁 {len(summary['arcs'])} arcs: {', '.join(summary['arcs'])}")
            if summary.get("episodes"):
                console.print(f"  🎬 {summary['episodes']} episodes")

            # POVs
            if summary["pov_distribution"]:
                povs = list(summary["pov_distribution"].keys())
                console.print(f"  👤 {len(povs)} POVs: {', '.join(povs)}")
        except Exception:
            pass  # Stats failed, just skip


@cli.command("search")
@click.argument("query")
@click.option("--db", "db_path", default="db", help="Path to LanceDB database")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["chapters", "entities", "relations"]),
    default="chapters",
)
@click.option("--arc", help="Filter by arc")
@click.option("--limit", default=10, help="Max results")
def search_cmd(query: str, db_path: str, search_type: str, arc: str | None, limit: int) -> None:
    """Search the database."""
    from .indexer import embed_query
    from .tools import search_semantic

    db = Database(db_path)

    if search_type == "chapters":
        query_vector = embed_query(query)
        results = asyncio.run(search_semantic(db, query_vector, arc=arc, limit=limit))

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(title=f"Search: {query}")
        table.add_column("Score", justify="right", width=6)
        table.add_column("Chapter", width=20)
        table.add_column("POV", width=12)
        table.add_column("Summary", width=50)

        for r in results:
            table.add_row(
                f"{r['score']:.2f}",
                f"{r['arc']} E{r['episode']}C{r['chapter']}",
                r["pov"],
                r["summary"][:50] + "...",
            )
        console.print(table)
    else:
        console.print(f"[yellow]Search type '{search_type}' not yet implemented.[/yellow]")


@cli.command("serve")
@click.option("--db", "db_path", default="db", help="Path to LanceDB database")
def serve_cmd(db_path: str) -> None:  # noqa: ARG001
    """Start the MCP server."""
    from .server import main

    main()


if __name__ == "__main__":
    cli()

#!/usr/bin/env python3
"""Demo script to test scanning and NER on real timeline content."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from echoes_mcp.indexer.scanner import scan_content
from echoes_mcp.indexer.spacy_utils import get_nlp
from echoes_mcp.tools.words_count import words_count


def main():
    demo_dir = Path(__file__).parent
    all_chapters = []

    for timeline in ["anima", "eros"]:
        content_path = demo_dir / timeline
        if not content_path.exists():
            print(f"⚠️  {timeline} not found (symlink broken?)")
            continue

        print(f"\n{'=' * 60}")
        print(f"📚 Timeline: {timeline.upper()}")
        print(f"{'=' * 60}")

        # Scan chapters
        chapters = scan_content(content_path)
        print(f"📖 Chapters found: {len(chapters)}")

        # Count total words
        total_words = 0
        arcs = set()
        povs = set()

        for ch in chapters:
            file_path = content_path / ch["file_path"]
            if file_path.exists():
                stats = words_count(file_path)
                total_words += stats["words"]
            arcs.add(ch["arc"])
            povs.add(ch["pov"])
            all_chapters.append((content_path, ch))

        print(f"📝 Total words: {total_words:,}")
        print(f"📁 Arcs: {sorted(arcs)}")
        print(f"👤 POVs: {sorted(povs)}")

        # Show first 5 chapters
        print("\n📋 First 5 chapters:")
        for ch in chapters[:5]:
            print(
                f"   - {ch['arc']}/ep{ch['episode']:02d}/ch{ch['chapter']:03d} [{ch['pov']}] {ch['title']}"
            )

    # Test NER on a sample chapter
    if all_chapters:
        print(f"\n{'=' * 60}")
        print("🔍 NER Demo (Named Entity Recognition)")
        print(f"{'=' * 60}")

        nlp = get_nlp()
        content_path, ch = all_chapters[0]
        file_path = content_path / ch["file_path"]
        text = ch["content"][:2000]  # First 2000 chars

        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        print(f"📄 Sample: {ch['arc']}/ep{ch['episode']:02d}/ch{ch['chapter']:03d}")
        print(f"🏷️  Entities found: {len(entities)}")
        # Group by type
        by_type: dict[str, set[str]] = {}
        for text, label in entities:
            by_type.setdefault(label, set()).add(text)
        for label, names in sorted(by_type.items()):
            print(f"   {label}: {', '.join(sorted(names)[:5])}")


if __name__ == "__main__":
    main()

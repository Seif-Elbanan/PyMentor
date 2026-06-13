from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    title: str
    section: str
    topic: str
    difficulty: str
    text: str


def load_chunks(directory: Path, chunk_words: int = 130, overlap: int = 25) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = _first_heading(text) or path.stem.replace("_", " ").title()
        sections = re.split(r"\n(?=## )", text)
        for section_index, section_text in enumerate(sections):
            section = _first_heading(section_text) or title
            metadata = _metadata(section_text)
            clean = re.sub(r"^---.*?---\s*", "", section_text, flags=re.DOTALL)
            words = clean.split()
            step = max(1, chunk_words - overlap)
            for offset in range(0, len(words), step):
                piece = words[offset : offset + chunk_words]
                if len(piece) < 20:
                    continue
                chunks.append(
                    Chunk(
                        chunk_id=f"{path.stem}-{section_index}-{offset // step}",
                        title=title,
                        section=section,
                        topic=metadata.get("topic", path.stem),
                        difficulty=metadata.get("difficulty", "beginner"),
                        text=" ".join(piece),
                    )
                )
    return chunks


def _first_heading(text: str) -> str:
    match = re.search(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _metadata(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in ("topic", "difficulty"):
        match = re.search(rf"^{key}:\s*(.+)$", text, flags=re.MULTILINE | re.IGNORECASE)
        if match:
            values[key] = match.group(1).strip().lower()
    return values

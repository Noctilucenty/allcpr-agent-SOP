"""Load and chunk the agent's local markdown knowledge base.

No paid APIs and no embeddings — this just reads the three in-repo markdown
files (``sop.md``, ``kb_seed.md``, ``sop_source_analysis.md``) and splits them
into heading-delimited chunks that the keyword retriever can score. Designed so
the same chunk list could later be fed to a vector DB without changing callers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

# The KB lives next to this module so it ships with the package.
KB_DIR = Path(__file__).resolve().parent
KB_FILES: Sequence[str] = ("sop.md", "kb_seed.md", "sop_source_analysis.md")


@dataclass(frozen=True)
class KBChunk:
    """One retrievable unit of the KB.

    ``source`` is the filename (used as the public citation), ``heading`` is the
    nearest markdown section title, and ``text`` is the section body including
    its heading line.
    """

    source: str
    heading: str
    text: str


def _split_sections(raw: str, source: str) -> List[KBChunk]:
    """Split one markdown document into level-2 (``## ``) sections.

    The preamble before the first ``## `` (typically the ``# Title`` + intro)
    becomes its own chunk. Empty sections are dropped.
    """
    chunks: List[KBChunk] = []
    heading = source  # label for the file preamble
    buf: List[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            chunks.append(KBChunk(source=source, heading=heading, text=body))

    for line in raw.splitlines():
        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
            buf = [line]
        else:
            buf.append(line)
    flush()
    return chunks


def load_chunks(kb_dir: Path | str = KB_DIR) -> List[KBChunk]:
    """Load every KB file under ``kb_dir`` and return heading-level chunks.

    Missing files are skipped silently so the agent still works if one optional
    doc is absent; ``sop.md`` and ``kb_seed.md`` are expected to be present.
    """
    base = Path(kb_dir)
    chunks: List[KBChunk] = []
    for name in KB_FILES:
        path = base / name
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        chunks.extend(_split_sections(raw, name))
    return chunks

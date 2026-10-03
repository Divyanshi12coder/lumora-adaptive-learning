"""Structure-aware chunking.

Text is split on paragraphs/headings first, then packed into windows of roughly
`size` words with `overlap` words carried over so a fact that straddles a
boundary is still retrievable. A Markdown heading always starts a new chunk
(overlap is never carried across sections) and is stored as chunk metadata
("section") so the UI can cite where an answer came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")


@dataclass
class Chunk:
    index: int
    text: str
    word_count: int
    meta: dict = field(default_factory=dict)


def _paragraphs(text: str) -> list[tuple[str, str | None]]:
    """Return (paragraph, current_heading) pairs."""
    out: list[tuple[str, str | None]] = []
    heading: str | None = None
    for block in re.split(r"\n\s*\n", text):
        body: list[str] = []
        for ln in (ln for ln in block.strip().split("\n") if ln.strip()):
            m = HEADING.match(ln)
            if m:
                if body:
                    out.append((" ".join(body), heading))
                    body = []
                heading = m.group(1).strip()
            else:
                body.append(ln.strip())
        if body:
            out.append((" ".join(body), heading))
    return out


def chunk_text(text: str, size: int = 120, overlap: int = 30) -> list[Chunk]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[Chunk] = []
    buf: list[str] = []  # words in the current window (may start with carried overlap)
    fresh = 0  # words added since the last flush
    section: str | None = None

    def flush(carry: bool) -> None:
        nonlocal buf, fresh
        if fresh > 0:
            chunks.append(Chunk(len(chunks), " ".join(buf), len(buf), {"section": section}))
        buf = buf[-overlap:] if (carry and overlap and fresh > 0) else []
        fresh = 0

    for para, heading in _paragraphs(text):
        if heading != section:
            flush(carry=False)
            section = heading
        for word in para.split():
            buf.append(word)
            fresh += 1
            if len(buf) >= size:
                flush(carry=True)
    flush(carry=False)
    return chunks

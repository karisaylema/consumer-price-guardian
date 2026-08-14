"""
Chunk the Consumer Protection Law text by article.

An article is the natural citation unit for legal text: when the agent answers,
it should be able to say "Art. 39 — Facturación de Consumo Excesivo" and have
that map to exactly one retrievable chunk. Fixed token windows would split a
single provision across two chunks and blur citations, so we chunk on the
article boundaries INEC's law text uses instead.

Pure text-in / chunks-out — no AWS, no embeddings — so the segmentation logic
(the part most likely to break on a reformatted source document) is unit
tested offline. PDF-to-text extraction happens upstream; this takes the text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# "Art. 39.-", "Art. 39.", "Artículo 39 .-", "ART. 39.-" ... capture the number
# and keep whatever heading text follows on the same line as a short label.
_ARTICLE_RE = re.compile(
    r"(?im)^\s*(?:art[íi]?culo|art)\.?\s*(\d+)\s*\.?\-?\s*(.*)$"
)

# Structural headings we carry as metadata so a retrieved article knows which
# TÍTULO / CAPÍTULO it sits under.
_TITULO_RE = re.compile(r"(?im)^\s*(t[íi]tulo\s+[ivxlcdm\d]+.*)$")
_CAPITULO_RE = re.compile(r"(?im)^\s*(cap[íi]tulo\s+[ivxlcdm\d]+.*)$")


@dataclass
class ArticleChunk:
    """One article, ready to embed and index."""

    article_number: int
    label: str                 # e.g. "Art. 39 — Facturación de Consumo Excesivo"
    titulo: str | None         # nearest preceding TÍTULO heading, if any
    capitulo: str | None       # nearest preceding CAPÍTULO heading, if any
    text: str                  # full article body, heading line included

    @property
    def citation(self) -> str:
        return f"Art. {self.article_number}"


def _clean(text: str) -> str:
    """Collapse whitespace within a chunk while preserving word boundaries."""
    return re.sub(r"[ \t]+", " ", text).strip()


def _short_heading(first_line_tail: str) -> str:
    """Turn the text after 'Art. N.-' into a short label, trimmed at the first
    sentence break so the label stays a title, not the whole first paragraph."""
    tail = first_line_tail.strip()
    # Legal headings are usually 'Título del artículo.- Cuerpo...'; keep up to
    # the first '.-' or sentence end.
    m = re.split(r"\.\-|\.\s|\:", tail, maxsplit=1)
    heading = m[0].strip(" .-") if m else tail
    return heading[:80]


def chunk_law(text: str) -> list[ArticleChunk]:
    """Split full law text into per-article chunks with structural metadata.

    Lines before the first article (preamble, considerandos) are ignored — they
    aren't citable articles. TÍTULO/CAPÍTULO headings update the running context
    applied to subsequent articles.
    """
    lines = text.splitlines()

    # Record where each article starts, plus the section context in force there.
    starts: list[tuple[int, int, str, str | None, str | None]] = []
    cur_titulo: str | None = None
    cur_capitulo: str | None = None
    # Legal headings span two lines ("CAPÍTULO V\nFACTURACIÓN"); after a heading
    # line we fold the next non-empty descriptive line into it as a subtitle.
    pending: str | None = None  # "titulo" | "capitulo" | None

    for i, line in enumerate(lines):
        if _TITULO_RE.match(line):
            cur_titulo, pending = _clean(line), "titulo"
            continue
        if _CAPITULO_RE.match(line):
            cur_capitulo, pending = _clean(line), "capitulo"
            continue

        m = _ARTICLE_RE.match(line)
        if m:
            pending = None
            number = int(m.group(1))
            heading = _short_heading(m.group(2))
            starts.append((i, number, heading, cur_titulo, cur_capitulo))
            continue

        if pending and line.strip():
            subtitle = _clean(line)
            if pending == "titulo":
                cur_titulo = f"{cur_titulo} — {subtitle}"
            else:
                cur_capitulo = f"{cur_capitulo} — {subtitle}"
            pending = None

    chunks: list[ArticleChunk] = []
    for idx, (line_no, number, heading, titulo, capitulo) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        body = _clean("\n".join(lines[line_no:end]))
        label = f"Art. {number}" + (f" — {heading}" if heading else "")
        chunks.append(ArticleChunk(
            article_number=number, label=label,
            titulo=titulo, capitulo=capitulo, text=body,
        ))
    return chunks

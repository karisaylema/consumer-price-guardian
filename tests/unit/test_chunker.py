"""Unit tests for the article chunker — the core of the legal RAG pipeline."""

from src.rag.chunker import chunk_law

SAMPLE_LAW = """\
LEY ORGÁNICA DE DEFENSA DEL CONSUMIDOR

Considerando que es deber del Estado proteger al consumidor... (preamble)

TÍTULO I
ÁMBITO Y OBJETO

CAPÍTULO I
PRINCIPIOS GENERALES

Art. 1.- Ámbito y Objeto.- Las disposiciones de la presente Ley son de orden
público y de interés social.

Art. 2.- Definiciones.- Para efectos de la presente Ley se entenderá por
consumidor a toda persona natural o jurídica.

TÍTULO II
DERECHOS Y OBLIGACIONES

CAPÍTULO V
FACTURACIÓN

Art. 39.- Facturación de Consumo Excesivo.- Cuando en un consumo se detecte una
elevación inusual, el proveedor deberá justificarla.
"""


def test_chunk_count_and_numbers():
    chunks = chunk_law(SAMPLE_LAW)
    assert [c.article_number for c in chunks] == [1, 2, 39]


def test_preamble_is_ignored():
    chunks = chunk_law(SAMPLE_LAW)
    # Nothing before Art. 1 should appear as its own chunk
    assert all("Considerando" not in c.text or c.article_number == 1 for c in chunks)
    assert chunks[0].article_number == 1


def test_labels_capture_heading():
    chunks = chunk_law(SAMPLE_LAW)
    art39 = next(c for c in chunks if c.article_number == 39)
    assert art39.label.startswith("Art. 39")
    assert "Facturación de Consumo Excesivo" in art39.label
    assert art39.citation == "Art. 39"


def test_section_metadata_tracks_running_context():
    chunks = chunk_law(SAMPLE_LAW)
    art1 = next(c for c in chunks if c.article_number == 1)
    art39 = next(c for c in chunks if c.article_number == 39)
    assert "TÍTULO I" in art1.titulo
    assert "CAPÍTULO I" in art1.capitulo
    # Art. 39 sits under the later headings
    assert "TÍTULO II" in art39.titulo
    assert "FACTURACIÓN" in art39.capitulo.upper()


def test_body_spans_to_next_article():
    chunks = chunk_law(SAMPLE_LAW)
    art39 = next(c for c in chunks if c.article_number == 39)
    assert "elevación inusual" in art39.text
    # should not bleed into a following article (there is none here)
    assert "Definiciones" not in art39.text


def test_empty_text_yields_no_chunks():
    assert chunk_law("") == []

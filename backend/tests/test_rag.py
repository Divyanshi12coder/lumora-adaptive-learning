import numpy as np
import pytest

from app.rag import store
from app.rag.chunker import chunk_text
from app.rag.embeddings import HashingEmbeddings
from app.rag.extract import ExtractionError, extract_text, sanitize_filename


def test_chunker_respects_size_overlap_and_sections():
    text = "# Intro\n\n" + " ".join(f"w{i}" for i in range(250)) + "\n\n# Next\n\n" + " ".join(f"x{i}" for i in range(50))
    chunks = chunk_text(text, size=100, overlap=20)
    assert all(c.word_count <= 100 for c in chunks)
    assert chunks[0].meta["section"] == "Intro"
    assert chunks[-1].meta["section"] == "Next"
    # overlap: last 20 words of chunk 0 start chunk 1
    assert chunks[1].text.split()[:20] == chunks[0].text.split()[-20:]
    # no overlap carried across a section boundary
    assert not chunks[-1].text.startswith("w")


def test_chunker_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("hello", size=10, overlap=10)


def test_hashing_embeddings_are_deterministic_normalised_and_meaningful():
    emb = HashingEmbeddings(384)
    a, b, c = emb.embed(["Plants use sunlight to make food", "Plants make food using sunlight", "Pharaohs ruled Egypt"])
    assert a == emb.embed_one("Plants use sunlight to make food")
    assert abs(np.linalg.norm(a) - 1) < 1e-6
    assert np.dot(a, b) > np.dot(a, c)


@pytest.mark.parametrize(
    "name,data,msg",
    [
        ("virus.exe", b"MZ....", "upload a .txt"),
        ("fake.pdf", b"not a pdf at all, just text pretending", "real PDF"),
        ("bin.txt", b"\x00\x01\x02" * 50, "binary"),
        ("tiny.txt", b"hi", "enough readable text"),
        ("empty.md", b"", "empty"),
    ],
)
def test_extraction_validation(name, data, msg):
    with pytest.raises(ExtractionError, match=msg):
        extract_text(name, data)


def test_extraction_accepts_text_and_sanitises_names():
    out = extract_text("notes.md", b"# Volcanoes\n\nA volcano is an opening in the Earth's crust where magma escapes.")
    assert out.content_type == "text/markdown"
    assert sanitize_filename("../../etc/pa<ss>wd.txt") == "pa_ss_wd.txt"


def test_vector_search_finds_the_right_lesson(client, db):
    results = store.search(db, "why do leaves need sunlight to make food", user_id=None, k=3)
    assert results, "expected seeded curriculum to be searchable"
    assert "Photosynthesis" in results[0].document_title
    assert results[0].score >= results[-1].score


def test_vector_search_topic_boost(client, db):
    from sqlalchemy import select

    from app.models import Topic

    shapes = db.scalar(select(Topic).where(Topic.slug == "shapes-geometry"))
    res = store.search(db, "how many sides", user_id=None, topic_id=shapes.id, k=2)
    assert res[0].topic_id == shapes.id

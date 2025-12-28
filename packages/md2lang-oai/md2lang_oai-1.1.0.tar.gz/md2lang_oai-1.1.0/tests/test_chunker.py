from md2lang_oai.chunker import chunk_text_by_paragraphs, estimate_tokens


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("word") == 1
    assert estimate_tokens("word word word word") == 4  # 16 chars / 4


def test_chunk_small_text():
    text = "Hello world"
    chunks = chunk_text_by_paragraphs(text, max_tokens=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_by_paragraphs():
    text = """Paragraph one.

Paragraph two.

Paragraph three."""
    chunks = chunk_text_by_paragraphs(text, max_tokens=10)
    # Should split into at least 2 chunks; exact count depends on token estimation
    assert len(chunks) >= 2
    assert "Paragraph one." in chunks[0]
    assert "Paragraph three." in chunks[-1]


def test_chunk_large_paragraph_by_lines():
    text = """Line one is short.
Line two is also short.
Line three is short too."""
    chunks = chunk_text_by_paragraphs(text, max_tokens=10)
    # Each line should be separated
    assert len(chunks) >= 3


def test_chunk_respects_max_tokens():
    # Build a large text
    text = " ".join(["word"] * 1000)  # 1000 words ~ 1000 tokens
    chunks = chunk_text_by_paragraphs(text, max_tokens=100)
    for chunk in chunks:
        assert estimate_tokens(chunk) <= 120  # allow some overhead

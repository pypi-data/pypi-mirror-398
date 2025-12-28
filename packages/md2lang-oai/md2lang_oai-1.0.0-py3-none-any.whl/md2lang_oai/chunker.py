from __future__ import annotations

from typing import List


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English/Latin scripts."""
    return len(text) // 4


def chunk_text_by_paragraphs(text: str, max_tokens: int) -> List[str]:
    """Split text into chunks that fit within max_tokens, respecting paragraph boundaries.

    Algorithm:
    - Split on double-newlines (paragraphs).
    - Accumulate paragraphs into chunks until adding the next would exceed max_tokens.
    - If a single paragraph exceeds max_tokens, split it by single newlines (lines).
    - If a single line exceeds max_tokens, split it by sentences (approximation: split on '. ').
    - If a single sentence exceeds max_tokens, force-split by characters.

    Returns:
        List of text chunks, each estimated to fit within max_tokens.
    """

    if estimate_tokens(text) <= max_tokens:
        return [text]

    chunks: List[str] = []
    paragraphs = text.split("\n\n")

    current_chunk_parts: List[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If this paragraph alone exceeds max, split it further
        if para_tokens > max_tokens:
            # Flush current chunk if any
            if current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))
                current_chunk_parts = []
                current_tokens = 0

            # Split paragraph by lines
            sub_chunks = _split_large_paragraph(para, max_tokens)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this paragraph would exceed max
        if current_tokens + para_tokens + 2 > max_tokens and current_chunk_parts:
            # Flush current chunk
            chunks.append("\n\n".join(current_chunk_parts))
            current_chunk_parts = []
            current_tokens = 0

        current_chunk_parts.append(para)
        current_tokens += para_tokens + 2  # +2 for "\n\n" separator tokens

    # Flush remaining
    if current_chunk_parts:
        chunks.append("\n\n".join(current_chunk_parts))

    return chunks


def _split_large_paragraph(para: str, max_tokens: int) -> List[str]:
    """Split a large paragraph by lines, then sentences, then force-split."""
    lines = para.split("\n")
    chunks: List[str] = []
    current_chunk_parts: List[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = estimate_tokens(line)

        if line_tokens > max_tokens:
            # Flush current
            if current_chunk_parts:
                chunks.append("\n".join(current_chunk_parts))
                current_chunk_parts = []
                current_tokens = 0

            # Split line by sentences
            sub_chunks = _split_large_line(line, max_tokens)
            chunks.extend(sub_chunks)
            continue

        if current_tokens + line_tokens + 1 > max_tokens and current_chunk_parts:
            chunks.append("\n".join(current_chunk_parts))
            current_chunk_parts = []
            current_tokens = 0

        current_chunk_parts.append(line)
        current_tokens += line_tokens + 1

    if current_chunk_parts:
        chunks.append("\n".join(current_chunk_parts))

    return chunks


def _split_large_line(line: str, max_tokens: int) -> List[str]:
    """Split a large line by sentences (approximation: '. '), then force-split."""
    sentences = line.split(". ")
    chunks: List[str] = []
    current_chunk_parts: List[str] = []
    current_tokens = 0

    for i, sent in enumerate(sentences):
        # Restore period unless it's the last sentence
        if i < len(sentences) - 1:
            sent = sent + "."

        sent_tokens = estimate_tokens(sent)

        if sent_tokens > max_tokens:
            # Flush current
            if current_chunk_parts:
                chunks.append(" ".join(current_chunk_parts))
                current_chunk_parts = []
                current_tokens = 0

            # Force-split by characters
            chunks.extend(_force_split(sent, max_tokens))
            continue

        if current_tokens + sent_tokens + 1 > max_tokens and current_chunk_parts:
            chunks.append(" ".join(current_chunk_parts))
            current_chunk_parts = []
            current_tokens = 0

        current_chunk_parts.append(sent)
        current_tokens += sent_tokens + 1

    if current_chunk_parts:
        chunks.append(" ".join(current_chunk_parts))

    return chunks


def _force_split(text: str, max_tokens: int) -> List[str]:
    """Force-split text by characters to fit within max_tokens."""
    max_chars = max_tokens * 4
    chunks: List[str] = []
    for i in range(0, len(text), max_chars):
        chunks.append(text[i : i + max_chars])
    return chunks

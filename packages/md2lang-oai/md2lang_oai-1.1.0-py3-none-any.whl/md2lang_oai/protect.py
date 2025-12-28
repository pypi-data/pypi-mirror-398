from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


_PLACEHOLDER_PREFIX = "@@MD2LANG_OAI_"
_PLACEHOLDER_SUFFIX = "@@"


@dataclass(frozen=True)
class ProtectedMapping:
    placeholders: Dict[str, str]


def protect_markdown(text: str) -> Tuple[str, ProtectedMapping]:
    """Protect Markdown regions that must not be translated.

    - Fenced code blocks delimited by lines starting with ```
    - Inline code spans delimited by backticks (supports multiple backticks)
    - Link/image URLs inside (...) are protected, while link text remains translatable.

    Returns:
        (protected_text, mapping)
    """

    placeholders: Dict[str, str] = {}
    pieces: List[str] = []
    i = 0
    counter = 0

    def new_placeholder(original: str) -> str:
        nonlocal counter
        key = f"{_PLACEHOLDER_PREFIX}{counter}{_PLACEHOLDER_SUFFIX}"
        counter += 1
        placeholders[key] = original
        return key

    def starts_fence_at(pos: int) -> bool:
        if pos == 0 or text[pos - 1] == "\n":
            return text.startswith("```", pos)
        return False

    def consume_fenced_block(pos: int) -> Tuple[str, int]:
        # Consume from opening ``` at line start through closing ``` at line start (or EOF)
        start = pos
        # Move to end of opening fence line
        line_end = text.find("\n", pos)
        if line_end == -1:
            return text[start:], len(text)
        pos = line_end + 1
        while pos < len(text):
            if starts_fence_at(pos):
                # consume closing fence line
                closing_line_end = text.find("\n", pos)
                if closing_line_end == -1:
                    return text[start:], len(text)
                return text[start : closing_line_end + 1], closing_line_end + 1
            # next line
            next_nl = text.find("\n", pos)
            if next_nl == -1:
                return text[start:], len(text)
            pos = next_nl + 1
        return text[start:], len(text)

    def consume_inline_code(pos: int) -> Tuple[str, int]:
        # Determine run of backticks
        tick_run = 1
        while pos + tick_run < len(text) and text[pos + tick_run] == "`":
            tick_run += 1
        delim = "`" * tick_run
        start = pos
        pos += tick_run
        end = text.find(delim, pos)
        if end == -1:
            return text[start:], len(text)
        return text[start : end + tick_run], end + tick_run

    def try_protect_link_url(pos: int) -> Tuple[bool, str, int]:
        # Protect only the URL part in ( ... ) for Markdown links/images.
        # Pattern handled: [label](url) and ![alt](url)
        # We are currently at '[' (or the '[' after '!').
        if text[pos] != "[":
            return False, "", pos
        close_bracket = text.find("]", pos + 1)
        if close_bracket == -1:
            return False, "", pos
        if close_bracket + 1 >= len(text) or text[close_bracket + 1] != "(":
            return False, "", pos
        close_paren = text.find(")", close_bracket + 2)
        if close_paren == -1:
            return False, "", pos

        label = text[pos : close_bracket + 1]  # includes [..]
        open_paren = text[close_bracket + 1]  # (
        url = text[close_bracket + 2 : close_paren]
        close_p = text[close_paren]  # )

        url_ph = new_placeholder(url)
        combined = f"{label}{open_paren}{url_ph}{close_p}"
        return True, combined, close_paren + 1

    while i < len(text):
        if starts_fence_at(i):
            block, j = consume_fenced_block(i)
            pieces.append(new_placeholder(block))
            i = j
            continue

        ch = text[i]
        if ch == "`":
            span, j = consume_inline_code(i)
            pieces.append(new_placeholder(span))
            i = j
            continue

        # Image: ![alt](url)
        if ch == "!" and i + 1 < len(text) and text[i + 1] == "[":
            ok, combined, j = try_protect_link_url(i + 1)
            if ok:
                pieces.append("!")
                pieces.append(combined)
                i = j
                continue

        # Link: [label](url)
        if ch == "[":
            ok, combined, j = try_protect_link_url(i)
            if ok:
                pieces.append(combined)
                i = j
                continue

        pieces.append(ch)
        i += 1

    protected_text = "".join(pieces)
    return protected_text, ProtectedMapping(placeholders=placeholders)


def restore_markdown(text: str, mapping: ProtectedMapping) -> str:
    restored = text
    # Restore in reverse-length order to avoid accidental partial replacements.
    for key in sorted(mapping.placeholders.keys(), key=len, reverse=True):
        restored = restored.replace(key, mapping.placeholders[key])
    return restored

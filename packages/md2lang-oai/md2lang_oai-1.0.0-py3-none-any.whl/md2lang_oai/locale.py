from __future__ import annotations

import re


_LOCALE_RE = re.compile(r"^(?P<lang>[a-zA-Z]{2})(?:-(?P<region>[a-zA-Z]{2}))?$")


def normalize_and_validate_locale(value: str) -> str:
    """Validate and normalize a locale.

    Supported forms:
    - xx (language)
    - xx-YY (language-region)

    Normalization:
    - language lowercased
    - region uppercased

    Raises:
        ValueError: if invalid.
    """

    value = (value or "").strip()
    match = _LOCALE_RE.match(value)
    if not match:
        raise ValueError(
            "Invalid locale. Use 'xx' or 'xx-YY' (e.g. 'es' or 'es-ES')."
        )

    lang = match.group("lang").lower()
    region = match.group("region")
    if region:
        return f"{lang}-{region.upper()}"
    return lang

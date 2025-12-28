import pytest

from md2lang_oai.locale import normalize_and_validate_locale


@pytest.mark.parametrize(
    "value,expected",
    [
        ("es", "es"),
        ("ES", "es"),
        (" es ", "es"),
        ("es-ES", "es-ES"),
        ("es-es", "es-ES"),
        ("pt-BR", "pt-BR"),
        ("pt-br", "pt-BR"),
    ],
)
def test_accepts_valid_locales(value, expected):
    assert normalize_and_validate_locale(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "e",
        "eng",
        "es_419",
        "es-",
        "-ES",
        "es-ESP",
        "es-es-ES",
        "es-123",
        "123",
    ],
)
def test_rejects_invalid_locales(value):
    with pytest.raises(ValueError):
        normalize_and_validate_locale(value)

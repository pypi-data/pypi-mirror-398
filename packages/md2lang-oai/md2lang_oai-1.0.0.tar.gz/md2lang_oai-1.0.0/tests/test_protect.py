from md2lang_oai.protect import protect_markdown, restore_markdown


def test_protects_fenced_code_blocks():
    s = """A

```js
console.log('x')
```

B
"""
    protected, mapping = protect_markdown(s)
    assert "console.log" not in protected
    restored = restore_markdown(protected, mapping)
    assert restored == s


def test_protects_inline_code_spans():
    s = "Use `code` here."
    protected, mapping = protect_markdown(s)
    assert "`code`" not in protected
    restored = restore_markdown(protected, mapping)
    assert restored == s


def test_protects_link_urls_but_not_label():
    s = "A [Label](https://example.com/x) end"
    protected, mapping = protect_markdown(s)
    assert "https://example.com/x" not in protected
    assert "[Label]" in protected
    restored = restore_markdown(protected, mapping)
    assert restored == s


def test_protects_image_urls_but_not_alt():
    s = "An ![Alt](https://img.example/a.png) end"
    protected, mapping = protect_markdown(s)
    assert "https://img.example/a.png" not in protected
    assert "![Alt]" in protected
    restored = restore_markdown(protected, mapping)
    assert restored == s

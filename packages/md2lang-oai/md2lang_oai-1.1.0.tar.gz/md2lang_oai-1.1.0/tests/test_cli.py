import json
from unittest.mock import patch

import httpx
from click.testing import CliRunner

from md2lang_oai.cli import main


def _mock_transport(assertions):
    def handler(request: httpx.Request) -> httpx.Response:
        assertions.append(request)
        assert "chat/completions" in str(request.url)
        assert "Authorization" in request.headers
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hola"}}]},
        )

    return httpx.MockTransport(handler)


def test_help_no_http(monkeypatch):
    called = []

    def boom(*args, **kwargs):
        called.append(True)
        raise AssertionError("Should not create http client")

    monkeypatch.setattr("md2lang_oai.oai.httpx.Client", boom)

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--to" in result.output
    assert called == []


def test_version_no_http(monkeypatch):
    called = []

    def boom(*args, **kwargs):
        called.append(True)
        raise AssertionError("Should not create http client")

    monkeypatch.setattr("md2lang_oai.oai.httpx.Client", boom)

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "md2lang-oai" in result.output
    assert called == []


def test_stdin_to_stdout_translation(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    requests = []
    transport = _mock_transport(requests)

    # Patch httpx.Client to always inject our mock transport
    with patch("md2lang_oai.oai.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            lambda *args, **kwargs: transport.handle_request(
                httpx.Request(
                    "POST",
                    kwargs.get("url") or args[0],
                    headers=kwargs.get("headers"),
                    json=kwargs.get("json"),
                )
            )
        )

        runner = CliRunner()
        result = runner.invoke(main, ["--to", "es-ES"], input="Hello")
        assert result.exit_code == 0, result.output
        assert result.output == "Hola"
        assert len(requests) == 1


def test_file_input_and_output(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    requests = []
    transport = _mock_transport(requests)

    with patch("md2lang_oai.oai.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            lambda *args, **kwargs: transport.handle_request(
                httpx.Request(
                    "POST",
                    kwargs.get("url") or args[0],
                    headers=kwargs.get("headers"),
                    json=kwargs.get("json"),
                )
            )
        )

        in_path = tmp_path / "in.md"
        out_path = tmp_path / "out.md"
        in_path.write_text("Hello", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--to", "es-ES", "--input", str(in_path), "--output", str(out_path)],
        )
        assert result.exit_code == 0, result.output
        assert out_path.read_text(encoding="utf-8") == "Hola"
        assert result.output == ""  # no stdout when using --output
        assert len(requests) == 1


def test_markdown_safety_preserves_code(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    # Return response that echoes input from request so we can inspect restoration behavior.
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads((request.content or b"{}").decode("utf-8"))
        user_content = body["messages"][1]["content"]
        sent = user_content.split("\nContent:\n", 1)[1]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": sent}}]},
        )

    transport = httpx.MockTransport(handler)

    with patch("md2lang_oai.oai.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            lambda *args, **kwargs: transport.handle_request(
                httpx.Request(
                    "POST",
                    kwargs.get("url") or args[0],
                    headers=kwargs.get("headers"),
                    json=kwargs.get("json"),
                )
            )
        )

        content = """Hello

```python
print('DO_NOT_TRANSLATE')
```

Inline `CODE` here.

A [Link Text](https://example.com/path) and ![Alt Text](https://img.example/a.png)
"""

        in_path = tmp_path / "in.md"
        out_path = tmp_path / "out.md"
        in_path.write_text(content, encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--to", "es-ES", "--input", str(in_path), "--output", str(out_path)],
        )
        assert result.exit_code == 0, result.output

        out = out_path.read_text(encoding="utf-8")
        assert "```python" in out
        assert "print('DO_NOT_TRANSLATE')" in out
        assert "`CODE`" in out
        assert "(https://example.com/path)" in out
        assert "(https://img.example/a.png)" in out

        # Ensure placeholders are not leaked
        assert "@@MD2LANG_OAI_" not in out


def test_custom_instructions_file(monkeypatch, tmp_path):
    """Test that custom instructions from file are included in the translation request."""
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    captured_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Translated output"}}]},
        )

    transport = httpx.MockTransport(handler)

    with patch("md2lang_oai.oai.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            lambda *args, **kwargs: transport.handle_request(
                httpx.Request(
                    "POST",
                    kwargs.get("url") or args[0],
                    headers=kwargs.get("headers"),
                    json=kwargs.get("json"),
                )
            )
        )

        in_path = tmp_path / "in.txt"
        in_path.write_text("Hello world", encoding="utf-8")

        instructions_path = tmp_path / "instructions.txt"
        instructions_path.write_text(
            "Regarding acronyms, translate STR as FUE, DEX as DES, CON as CON, WIS as SAB and CHA as CAR",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--to",
                "es-ES",
                "--input",
                str(in_path),
                "--instructions-file",
                str(instructions_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert len(captured_requests) == 1

        # Verify the custom instructions are in the system message
        req_body = json.loads(captured_requests[0].content.decode("utf-8"))
        system_message = req_body["messages"][0]["content"]
        assert "Additional instructions:" in system_message
        assert "STR as FUE" in system_message
        assert "DEX as DES" in system_message


def test_translation_without_custom_instructions(monkeypatch, tmp_path):
    """Test that translation works without custom instructions (backward compatibility)."""
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    captured_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Translated output"}}]},
        )

    transport = httpx.MockTransport(handler)

    with patch("md2lang_oai.oai.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
            lambda *args, **kwargs: transport.handle_request(
                httpx.Request(
                    "POST",
                    kwargs.get("url") or args[0],
                    headers=kwargs.get("headers"),
                    json=kwargs.get("json"),
                )
            )
        )

        in_path = tmp_path / "in.txt"
        in_path.write_text("Hello world", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--to", "es-ES", "--input", str(in_path)],
        )
        assert result.exit_code == 0, result.output
        assert len(captured_requests) == 1

        # Verify there are no additional instructions in the system message
        req_body = json.loads(captured_requests[0].content.decode("utf-8"))
        system_message = req_body["messages"][0]["content"]
        assert "Additional instructions:" not in system_message

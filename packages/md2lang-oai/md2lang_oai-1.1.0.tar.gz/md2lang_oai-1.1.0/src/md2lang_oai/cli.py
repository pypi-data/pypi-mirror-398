from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

import click

from md2lang_oai.chunker import chunk_text_by_paragraphs
from md2lang_oai.locale import normalize_and_validate_locale
from md2lang_oai.oai import OpenAIChatCompletionsClient
from md2lang_oai.protect import protect_markdown, restore_markdown


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_MAX_TOKENS = 3000
DEFAULT_TIMEOUT = 300.0


@dataclass(frozen=True)
class IOPaths:
    input_path: Optional[str]
    output_path: Optional[str]


def _read_all_input(input_path: Optional[str]) -> str:
    if input_path:
        with open(input_path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def _write_all_output(output_path: Optional[str], content: str) -> None:
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return
    sys.stdout.write(content)


def _resolve_api_key(env_name: str) -> str:
    value = os.environ.get(env_name)
    if not value:
        raise click.ClickException(
            f"Missing API key: environment variable {env_name!r} is not set."
        )
    return value


def _version() -> str:
    from importlib.metadata import version

    return version("md2lang-oai")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=_version(), prog_name="md2lang-oai")
@click.option("--to", "to_locale", required=True, metavar="LOCALE", help="Target locale: xx or xx-YY (e.g. es or es-ES).")
@click.option("--input", "input_path", type=click.Path(dir_okay=False, path_type=str), default=None, help="Read input from a file instead of stdin.")
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False, path_type=str), default=None, help="Write output to a file instead of stdout.")
@click.option("--instructions-file", "instructions_file", type=click.Path(exists=True, dir_okay=False, path_type=str), default=None, help="Path to a file with additional translation instructions.")
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Chat Completions model name.")
@click.option("--base-url", default=DEFAULT_BASE_URL, show_default=True, help="OpenAI-compatible base URL (e.g. https://api.openai.com/v1).")
@click.option("--api-key-env", default=DEFAULT_API_KEY_ENV, show_default=True, help="Environment variable name holding the API key.")
@click.option("--max-tokens", default=DEFAULT_MAX_TOKENS, show_default=True, type=int, help="Max tokens per chunk (splits large inputs to fit model context).")
@click.option("--timeout", default=DEFAULT_TIMEOUT, show_default=True, type=float, help="HTTP request timeout in seconds.")
def main(
    to_locale: str,
    input_path: Optional[str],
    output_path: Optional[str],
    instructions_file: Optional[str],
    model: str,
    base_url: str,
    api_key_env: str,
    max_tokens: int,
    timeout: float,
) -> None:
    """Translate Markdown/text into a target locale (pipe-friendly)."""

    try:
        locale = normalize_and_validate_locale(to_locale)
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    api_key = _resolve_api_key(api_key_env)

    custom_instructions = None
    if instructions_file:
        try:
            custom_instructions = _read_all_input(instructions_file)
        except (OSError, UnicodeError) as e:
            raise click.ClickException(f"Failed to read instructions file '{instructions_file}': {e}") from e

    try:
        raw = _read_all_input(input_path)
    except (OSError, UnicodeError) as e:
        source = input_path if input_path is not None else "<stdin>"
        raise click.ClickException(f"Failed to read input from {source}: {e}") from e

    # Chunk input if needed
    chunks = chunk_text_by_paragraphs(raw, max_tokens=max_tokens)
    if len(chunks) > 1:
        click.echo(f"Splitting input into {len(chunks)} chunks...", err=True)

    client = OpenAIChatCompletionsClient(base_url=base_url, api_key=api_key, timeout_s=timeout)
    translated_chunks = []

    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            click.echo(f"Translating chunk {i}/{len(chunks)}...", err=True)

        protected, mapping = protect_markdown(chunk)

        try:
            translated = client.translate(
                text=protected,
                to_locale=locale,
                model=model,
                custom_instructions=custom_instructions,
            )
        except Exception as e:
            raise click.ClickException(str(e)) from e

        restored = restore_markdown(translated, mapping)
        translated_chunks.append(restored)

    # Reassemble chunks
    final_output = "\n\n".join(translated_chunks)

    _write_all_output(output_path, final_output)

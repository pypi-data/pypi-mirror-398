# md2lang-oai

Minimal CLI that translates Markdown/text into a target locale using an OpenAI-compatible **Chat Completions** HTTP endpoint.

## Install / run (uv)

Run without installing:

```bash
uv run md2lang-oai --help
```

## Usage

Translate from stdin to stdout:

```bash
echo "Hello" | uv run md2lang-oai --to es-ES
```

Translate a file:

```bash
uv run md2lang-oai --to es-ES --input README.md
```

Write to a file:

```bash
uv run md2lang-oai --to es-ES --input input.md --output output.md
```

Pipe-friendly (stdin):

```bash
cat input.md | uv run md2lang-oai --to es-ES > output.md
```

## Configuration

- API key is read from `OPENAI_API_KEY` by default.
- Choose a different env var name with `--api-key-env`.
- Override the endpoint with `--base-url` (must be OpenAI-compatible).
- Choose a model with `--model`.
- Adjust timeout with `--timeout` (default: 300s for slow/local models).
- Control chunking with `--max-tokens` (default: 3000 tokens per chunk).

Example:

```bash
export OPENAI_API_KEY="..."
uv run md2lang-oai --to es-ES --model gpt-4o-mini --base-url https://api.openai.com/v1 < input.md
```

### Large files and context limits

If your input exceeds the model's context window, the CLI automatically splits it into chunks by paragraph boundaries. Each chunk is translated separately and reassembled. Adjust `--max-tokens` to fit your model's limit (e.g., 3000 for small models, 8000+ for larger ones).

Example for a local Ollama model with a 4K context:

```bash
export OPENAI_API_KEY=test
uv run md2lang-oai --to es-ES --model openchat:7b --base-url http://localhost:11434/v1 --max-tokens 2000 --timeout 600 --input large-file.md --output large-file-es.md
```

## Markdown handling

The tool preserves Markdown structure as much as possible:

- Does **not** translate inside fenced code blocks (`...`).
- Does **not** translate inline code spans (`like this`).
- Keeps link/image syntax intact; URLs are never translated.

## Development

Run tests:

```bash
uv run pytest
```

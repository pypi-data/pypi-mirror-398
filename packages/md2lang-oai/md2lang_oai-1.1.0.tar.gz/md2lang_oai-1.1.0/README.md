# md2lang-oai

Minimal CLI that translates Markdown/text into a target locale using an OpenAI-compatible **Chat Completions** HTTP endpoint.

## Quick start

Run without installing:

```bash
uvx md2lang-oai --help
```

## Usage

Translate from stdin to stdout:

```bash
echo "Hello" | uvx md2lang-oai --to es-ES
```

Translate a file:

```bash
uvx md2lang-oai --to es-ES --input README.md
```

Write to a file:

```bash
uvx md2lang-oai --to es-ES --input input.md --output output.md
```

Pipe-friendly (stdin):

```bash
cat input.md | uvx md2lang-oai --to es-ES > output.md
```

Provide custom translation instructions:

```bash
uvx md2lang-oai --to es-ES --input dnd_adventure.md --instructions-file dnd_instructions.txt
```

## Configuration

- API key is read from `OPENAI_API_KEY` by default.
- Choose a different env var name with `--api-key-env`.
- Override the endpoint with `--base-url` (must be OpenAI-compatible).
- Choose a model with `--model`.
- Adjust timeout with `--timeout` (default: 300s for slow/local models).
- Control chunking with `--max-tokens` (default: 3000 tokens per chunk).
- Provide custom translation instructions with `--instructions-file` (e.g., for domain-specific terminology).

Example:

```bash
export OPENAI_API_KEY="..."
uvx md2lang-oai --to es-ES --model gpt-4o-mini < input.md
```

### Large files and context limits

If your input exceeds the model's context window, the CLI automatically splits it into chunks by paragraph boundaries. Each chunk is translated separately and reassembled. Adjust `--max-tokens` to fit your model's limit (e.g., 3000 for small models, 8000+ for larger ones).

Example for a local Ollama model with a 4K context:

```bash
export OPENAI_API_KEY=test
uvx md2lang-oai --to es-ES --model openchat:7b --base-url http://localhost:11434/v1 --max-tokens 2000 --timeout 600 --input large-file.md --output large-file-es.md
```

### Custom translation instructions

You can provide domain-specific instructions to guide the translation process. For instance, when translating a tabletop role-playing adventure, you may want specific acronyms to be translated in a particular way:

Create a file `dnd_instructions.txt`:

```
Regarding acronyms, translate:
- STR as FUE
- DEX as DES
- CON as CON
- WIS as SAB
- CHA as CAR
```

Then use it:

```bash
uvx md2lang-oai --to es-ES --input dnd_adventure.md --instructions-file dnd_instructions.txt
```

The instructions can be plain text or Markdown and will be appended to the system prompt sent to the model.

### Markdown handling

The tool preserves Markdown structure as much as possible:

- Does **not** translate inside fenced code blocks (`...`).
- Does **not** translate inline code spans (`like this`).
- Keeps link/image syntax intact; URLs are never translated.

## Development

Install dependencies and create a virtual environment:

```bash
uv sync
```

This will create a `.venv` directory with all dependencies installed.

Run tests:

```bash
uv run pytest
```

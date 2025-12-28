# Agent guidance (md2lang-oai)

This repo is intentionally small.

## Non-negotiables

- Keep it minimal: KISS, procedural Python.
- CLI-first UX: good `--help`, clear errors, pipe-friendly.
- Tests are mandatory for every behavioral change.
- No feature creep: no subcommands, config files, caching, plugin systems, or multi-provider frameworks.
- Keep public APIs small and stable.
- Use Conventional Commits format for all commit messages.

## Tooling constraints

- Python 3.10+
- Dependency manager: `uv`
- Build backend: `hatchling`
- Dependencies: `click` for CLI, `httpx` for HTTP. Add nothing else unless strongly justified.

## Behavior

- Default output is translated content only to stdout.
- Any diagnostics must go to stderr.
- Tests must never make real network calls; use `httpx.MockTransport`.

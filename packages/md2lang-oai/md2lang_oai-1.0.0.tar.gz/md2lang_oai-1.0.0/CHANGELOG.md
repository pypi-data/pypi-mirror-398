# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-24

### Added

- `md2lang-oai` CLI translating Markdown/text to a target locale via an OpenAI-compatible Chat Completions endpoint.
- Locale validation for `xx` and `xx-YY`.
- Markdown safety: preserves fenced code blocks and inline code spans.
- Test suite using `pytest` + `httpx.MockTransport`.

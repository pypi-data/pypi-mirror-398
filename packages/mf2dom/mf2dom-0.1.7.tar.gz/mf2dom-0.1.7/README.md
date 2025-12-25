# mf2dom

Microformats2 (mf2) parser and deterministic renderer powered by JustHTML.

`mf2dom` focuses on:
- Correct mf2 parsing (validated against the official `microformats-tests` suite)
- Deterministic HTML rendering and stable round-trips (`HTML -> mf2 -> HTML`)
- A small runtime surface area (no network I/O, no BeautifulSoup)

## Installation

```bash
pip install mf2dom
```

Requires Python 3.11+.

## Quickstart

Parse mf2 JSON from HTML:

```python
import mf2dom

html = '<a class="h-card u-url p-name" href="/me">Alice</a>'
doc = mf2dom.parse(html, base_url="https://example.com/")
print(doc["items"])
```

The parsed document is a dict with `items`, `rels`, and `rel-urls` keys (mf2 JSON shape).

Render mf2 JSON back into canonical HTML:

```python
html2 = mf2dom.render(doc)
```

Async parsing (offloads to a thread):

```python
doc = await mf2dom.parse_async(html, base_url="https://example.com/")
```

## API

- `mf2dom.parse(html, *, base_url=None, url=None) -> dict`
  - `html` can be a string/bytes, a `justhtml.JustHTML` instance, or a JustHTML root node.
  - `base_url` controls resolution of relative URLs (preferred). `url` is a deprecated alias.
- `mf2dom.parse_async(...)` is `parse(...)` via `asyncio.to_thread(...)`.
- `mf2dom.render(doc) -> str` renders a deterministic HTML representation of an mf2 document.

## Why mf2dom vs mf2py?

Both libraries parse microformats, but they optimize for different use cases:

- Choose `mf2dom` if you need deterministic rendering, stable round-trips, and a smaller/no-network
  runtime surface (useful for normalization, caching, and “canonical mf2 HTML” fixtures).
- Choose `mf2py` if you need URL fetching, microformats1 compatibility, metaformats support, or
  wider Python version support.

## Testing & correctness

- Official parsing fixtures: `tests/test_official_microformats_suite.py` runs the upstream
  `microformats-tests` JSON fixtures.
- Coverage gate: `pyproject.toml` enforces 100% branch coverage.

To run the official fixture suite locally, check out `microformats-tests` as a sibling directory:

```bash
git clone https://github.com/microformats/microformats-tests ../microformats-tests
```

## Development (uv)

```bash
uv sync --group dev
uv run pytest
uv run coverage run -m pytest && uv run coverage report
uv run pre-commit install
```

## License

AGPL 3

"""URL utilities (joining and `srcset` parsing)."""

from __future__ import annotations

import re
from urllib.parse import urljoin


def try_urljoin(base: str | None, url: str | None, *, allow_fragments: bool = True) -> str | None:
    if url is None:
        return None
    if url.startswith(("https://", "http://")):
        return url
    if not base:
        return url
    try:
        return urljoin(base, url, allow_fragments=allow_fragments)
    except ValueError:
        return url


_SRCSET_RE = re.compile(r"(\S+)\s*([\d.]+[xw])?\s*,?\s*", re.MULTILINE)


def parse_srcset(srcset: str, base_url: str | None) -> dict[str, str]:
    sources: dict[str, str] = {}
    for url, descriptor in _SRCSET_RE.findall(srcset):
        key = descriptor or "1x"
        if key not in sources:
            sources[key] = try_urljoin(base_url, url.strip(",")) or url.strip(",")
    return sources

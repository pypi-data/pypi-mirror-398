"""Text extraction utilities used by mf2 parsing.

This implements a DOM-like `textContent` traversal with mf2-specific rules for
dropping certain elements and optionally replacing `<img>` elements.
"""

from __future__ import annotations

from typing import Any

from .dom import get_attr, is_element, iter_child_nodes
from .urls import try_urljoin

_DROP_TAGS = {"script", "style", "template"}


def text_content(
    node: Any,
    *,
    replace_img: bool = False,
    img_to_src: bool = True,
    base_url: str | None = None,
) -> str:
    """Return DOM-like textContent for a subtree.

    This intentionally preserves whitespace exactly as it appears in text nodes.
    """

    parts: list[str] = []
    stack: list[Any] = [node]

    while stack:
        cur = stack.pop()
        name = getattr(cur, "name", "")

        if name in {"#comment", "!doctype"}:
            continue

        if name == "#text":
            data = getattr(cur, "data", None)
            if isinstance(data, str):
                parts.append(data)
            continue

        if is_element(cur):
            tag = cur.name.lower()
            if tag in _DROP_TAGS:
                continue

            if tag == "img" and replace_img:
                alt = get_attr(cur, "alt")
                if alt is None and img_to_src:
                    src = get_attr(cur, "src")
                    if src is not None:
                        alt = try_urljoin(base_url, src) or src
                if alt is not None:
                    parts.append(" ")
                    parts.append(alt)
                    parts.append(" ")
                continue

        if hasattr(cur, "children"):
            # Depth-first traversal in document order.
            stack.extend(reversed(list(iter_child_nodes(cur))))

    return "".join(parts)

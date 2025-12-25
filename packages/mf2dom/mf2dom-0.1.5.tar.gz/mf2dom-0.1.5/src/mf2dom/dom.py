"""DOM helpers for JustHTML nodes.

JustHTML exposes a lightweight DOM-like tree. This module provides:
- Safe element detection
- Deterministic traversal helpers
- HTML `class` parsing that follows the HTML spec (ASCII whitespace only)

Important: `class` tokens are returned in document order (a list), because some
microformats parsing rules are order-sensitive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Iterator


class HasDom(Protocol):
    name: str
    parent: Any | None

    @property
    def children(self) -> list[Any]: ...  # pragma: no cover


class Element(HasDom, Protocol):
    attrs: dict[str, str | None]

    def to_html(
        self, *, pretty: bool = True, indent_size: int = 2, indent: int = 0
    ) -> str: ...  # pragma: no cover


def is_element(node: Any) -> bool:
    name = str(getattr(node, "name", ""))
    if not name or name.startswith(("#", "!")):
        return False
    return isinstance(getattr(node, "attrs", None), dict)


def iter_child_nodes(node: HasDom) -> Iterator[Any]:
    """Yield child nodes (including text/comment/doctype nodes)."""
    children = getattr(node, "children", None)
    if children:
        yield from children


def iter_child_elements(node: HasDom) -> Iterator[Element]:
    """Yield element children, skipping `<template>` elements."""
    for child in iter_child_nodes(node):
        if is_element(child) and getattr(child, "name", "").lower() != "template":
            yield child


def iter_descendants(node: HasDom) -> Iterator[Any]:
    """Yield descendant nodes in document order (depth-first)."""
    stack: list[Any] = list(reversed(list(iter_child_nodes(node))))
    while stack:
        cur = stack.pop()
        yield cur
        if hasattr(cur, "children"):
            stack.extend(reversed(list(iter_child_nodes(cur))))


def iter_descendant_elements(node: HasDom) -> Iterator[Element]:
    """Yield descendant elements, skipping `<template>` elements."""
    for cur in iter_descendants(node):
        if is_element(cur) and getattr(cur, "name", "").lower() != "template":
            yield cur


def iter_preorder_elements(root: Element) -> Iterator[Element]:
    """Yield `root` then its descendant elements (pre-order)."""
    yield root
    yield from iter_descendant_elements(root)


def get_attr(el: Element, name: str) -> str | None:
    """Get an attribute value (or None if missing)."""
    return el.attrs.get(name)


def set_attr(el: Element, name: str, value: str | None) -> None:
    """Set an attribute value (use None for boolean attributes)."""
    el.attrs[name] = value


def get_classes(el: Element) -> list[str]:
    """Return `class` tokens in document order.

    Per HTML, class attributes are split on ASCII whitespace only
    (` \\t\\n\\f\\r`). Non-ASCII whitespace characters are treated as part of the token.
    """
    raw = get_attr(el, "class")
    if not raw:
        return []
    # Per HTML, class is split on ASCII whitespace only.
    raw = raw.strip(" \t\n\f\r")
    if not raw:
        return []
    return [c for c in _ASCII_WHITESPACE_RE.split(raw) if c]


_ASCII_WHITESPACE_RE = re.compile(r"[ \t\n\f\r]+")


def has_any_class(el: Element, names: Iterable[str]) -> bool:
    classes = set(get_classes(el))
    return any(name in classes for name in names)


def has_class_prefix(el: Element, prefixes: Iterable[str]) -> bool:
    """Return True if any class token starts with one of `prefixes`."""
    prefix_tuple = tuple(prefixes)
    return any(cls.startswith(prefix_tuple) for cls in get_classes(el))


def ancestor_elements(el: Element) -> Iterator[Element]:
    """Yield ancestor elements starting from the parent."""
    cur: Any | None = el.parent
    while cur is not None:
        if is_element(cur):
            yield cur
        cur = getattr(cur, "parent", None)


@dataclass(frozen=True, slots=True)
class ValueClassNodes:
    nodes: list[Element]

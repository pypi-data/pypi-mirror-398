"""Implied property parsing (name/photo/url).

Implied properties are applied when an mf2 item has no explicit corresponding
properties, per the mf2 parsing algorithm.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .classes import has_root_class, is_valid_property_class
from .dom import Element, get_attr, get_classes, iter_child_elements
from .text import text_content
from .urls import parse_srcset, try_urljoin

if TYPE_CHECKING:  # pragma: no cover
    from .types import UrlObject, UrlValue


def _is_microformat_root(el: Element) -> bool:
    return has_root_class(get_classes(el))


def _has_property_class(el: Element) -> bool:
    return any(is_valid_property_class(cls) for cls in get_classes(el))


def _is_implied_candidate(el: Element) -> bool:
    return not _is_microformat_root(el) and not _has_property_class(el)


_WHITESPACE_RE = re.compile(r"\s+")


def implied_name(root: Element, base_url: str | None) -> str:
    """Compute implied `name` for an item root."""

    def non_empty(val: str | None) -> bool:
        return val is not None and val != ""

    def normalize_ws(val: str) -> str:
        return _WHITESPACE_RE.sub(" ", val).strip()

    if root.name.lower() in {"img", "area"}:
        alt = get_attr(root, "alt")
        if alt is not None:
            return normalize_ws(alt)

    if root.name.lower() == "abbr":
        title = get_attr(root, "title")
        if title is not None:
            return normalize_ws(title)

    children = list(iter_child_elements(root))
    candidate: Element | None = None
    if len(children) == 1:
        candidate = children[0]
        if _is_microformat_root(candidate):
            candidate = None
        elif candidate.name.lower() not in {"img", "area", "abbr"}:
            grand = list(iter_child_elements(candidate))
            if len(grand) == 1:
                candidate = grand[0]
                if candidate.name.lower() not in {"img", "area", "abbr"} or _is_microformat_root(
                    candidate
                ):
                    candidate = None

    if candidate is not None:
        if candidate.name.lower() in {"img", "area"}:
            alt = get_attr(candidate, "alt")
            if non_empty(alt):
                return normalize_ws(alt or "")
        if candidate.name.lower() == "abbr":
            title = get_attr(candidate, "title")
            if non_empty(title):
                return normalize_ws(title or "")

    return normalize_ws(text_content(root, replace_img=True, img_to_src=False, base_url=base_url))


def _img_value(img: Element, base_url: str | None) -> UrlValue | None:
    src = get_attr(img, "src")
    if src is None:
        return None
    abs_src = try_urljoin(base_url, src) or src
    alt = get_attr(img, "alt")
    srcset = get_attr(img, "srcset")
    if alt is not None or srcset:
        out: UrlObject = {"value": abs_src}
        if alt is not None:
            out["alt"] = alt
        if srcset:
            out["srcset"] = parse_srcset(srcset, base_url)
        return out
    return abs_src


def implied_photo(root: Element, base_url: str | None) -> UrlValue | None:
    """Compute implied `photo` for an item root."""
    if root.name.lower() == "img":
        return _img_value(root, base_url)
    if root.name.lower() == "object":
        data = get_attr(root, "data")
        if data is not None:
            return try_urljoin(base_url, data) or data

    def has_u_property(el: Element) -> bool:
        return any(cls.startswith("u-") and is_valid_property_class(cls) for cls in get_classes(el))

    def photo_child(children: list[Element]) -> Element | None:
        imgs = [c for c in children if c.name.lower() == "img"]
        if len(imgs) == 1 and not _is_microformat_root(imgs[0]) and not has_u_property(imgs[0]):
            return imgs[0]
        objs = [c for c in children if c.name.lower() == "object"]
        if len(objs) == 1 and not _is_microformat_root(objs[0]) and not has_u_property(objs[0]):
            return objs[0]
        return None

    children = list(iter_child_elements(root))
    candidate = photo_child(children)
    if candidate is None and len(children) == 1 and not _is_microformat_root(children[0]):
        candidate = photo_child(list(iter_child_elements(children[0])))

    if candidate is None:
        return None

    if candidate.name.lower() == "img":
        return _img_value(candidate, base_url)
    data = get_attr(candidate, "data")
    if data is not None:
        return try_urljoin(base_url, data) or data
    return None


def implied_url(root: Element, base_url: str | None) -> str | None:
    """Compute implied `url` for an item root."""
    if root.name.lower() in {"a", "area"}:
        href = get_attr(root, "href")
        if href is not None:
            return try_urljoin(base_url, href) or href

    def has_u_property(el: Element) -> bool:
        return any(cls.startswith("u-") and is_valid_property_class(cls) for cls in get_classes(el))

    def url_child(children: list[Element]) -> Element | None:
        as_ = [c for c in children if c.name.lower() == "a"]
        if len(as_) == 1 and not _is_microformat_root(as_[0]) and not has_u_property(as_[0]):
            return as_[0]
        areas = [c for c in children if c.name.lower() == "area"]
        if len(areas) == 1 and not _is_microformat_root(areas[0]) and not has_u_property(areas[0]):
            return areas[0]
        return None

    children = list(iter_child_elements(root))
    candidate = url_child(children)
    if candidate is None and len(children) == 1 and not _is_microformat_root(children[0]):
        candidate = url_child(list(iter_child_elements(children[0])))
    if candidate is None:
        return None

    href = get_attr(candidate, "href")
    if href is None:
        return None
    return try_urljoin(base_url, href) or href

"""Microformats2 parser.

Implements the mf2 parsing algorithm:
https://microformats.org/wiki/microformats2-parsing

Entry points:
- `parse(...)` for synchronous parsing
- `parse_async(...)` for running parsing off-thread
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from justhtml import JustHTML

from .dom import (
    Element,
    HasDom,
    ancestor_elements,
    get_attr,
    iter_child_elements,
    iter_descendant_elements,
)
from .implied import implied_name, implied_photo, implied_url
from .properties import (
    is_microformat_root,
    parse_dt,
    parse_e,
    parse_p,
    parse_u,
    property_classes,
    root_types,
)
from .text import text_content
from .types import EValue, Mf2Document, Mf2Item
from .urls import try_urljoin

if TYPE_CHECKING:  # pragma: no cover
    from .types import PropertyValue, RelUrl


@dataclass(slots=True)
class _ParseContext:
    base_url: str | None
    document_lang: str | None


HtmlInput: TypeAlias = str | bytes | bytearray | memoryview | JustHTML | HasDom


def _first_lang(doc_root: HasDom) -> str | None:
    for el in iter_descendant_elements(doc_root):
        if el.name.lower() == "html":
            return get_attr(el, "lang")
    return None


def _discover_base_url(doc_root: HasDom, *, base_url: str | None) -> str | None:
    for el in iter_descendant_elements(doc_root):
        if el.name.lower() != "base":
            continue
        href = get_attr(el, "href")
        if not href:
            break
        # Absolute replaces; relative is joined against provided URL if any.
        joined = try_urljoin(base_url, href)
        base_url = joined or href
        break
    return base_url


def _split_tokens(value: str | None) -> list[str]:
    if not value:
        return []
    return [t for t in value.split() if t]


_REL_ATTRS: tuple[Literal["media"], Literal["hreflang"], Literal["type"], Literal["title"]] = (
    "media",
    "hreflang",
    "type",
    "title",
)


def _parse_rels(
    doc_root: HasDom, *, base_url: str | None
) -> tuple[dict[str, list[str]], dict[str, RelUrl]]:
    rels: dict[str, list[str]] = defaultdict(list)
    rel_urls: dict[str, RelUrl] = {}

    for el in iter_descendant_elements(doc_root):
        if el.name.lower() not in {"a", "area", "link"}:
            continue
        rel_attr = get_attr(el, "rel")
        if not rel_attr:
            continue
        href = get_attr(el, "href")
        if href is None:
            continue
        abs_href = try_urljoin(base_url, href) or href
        rel_tokens = _split_tokens(rel_attr)
        if not rel_tokens:
            continue

        for rel in rel_tokens:
            if abs_href not in rels[rel]:
                rels[rel].append(abs_href)

        entry = rel_urls.setdefault(abs_href, {"rels": []})
        entry_rels = entry["rels"]
        for rel in rel_tokens:
            if rel not in entry_rels:
                entry_rels.append(rel)

        if "text" not in entry:
            entry["text"] = text_content(el)

        for attr in _REL_ATTRS:
            v = get_attr(el, attr)
            if v is not None and v != "":
                entry.setdefault(attr, v)

    return dict(rels), rel_urls


def _has_ancestor_microformat_root(el: Element) -> bool:
    return any(is_microformat_root(a) for a in ancestor_elements(el))


def _top_level_roots(doc_root: HasDom) -> list[Element]:
    roots: list[Element] = []
    for el in iter_descendant_elements(doc_root):
        if not is_microformat_root(el):
            continue
        if _has_ancestor_microformat_root(el):
            continue
        roots.append(el)
    return roots


def _is_property_for_parent(el: Element) -> bool:
    return bool(property_classes(el))


def _parse_item(
    el: Element,
    ctx: _ParseContext,
    *,
    parent_lang: str | None,
    ignore_root_property_classes: frozenset[str] = frozenset(),
) -> Mf2Item:
    types = root_types(el)
    item: Mf2Item = {"type": types, "properties": {}}

    element_id = get_attr(el, "id")
    if element_id:
        item["id"] = element_id

    root_lang = get_attr(el, "lang") or parent_lang
    children: list[Mf2Item] = []

    props: dict[str, list[PropertyValue]] = defaultdict(list)
    default_date: str | None = None
    has_p = False
    has_u = False
    has_e = False
    has_nested_microformat = False

    def add_prop(name: str, value: PropertyValue) -> None:
        props[name].append(value)

    def simple_value(prop_class: str, target: Element) -> PropertyValue:
        nonlocal default_date
        if prop_class.startswith("p-"):
            return parse_p(target, base_url=ctx.base_url)  # pragma: no cover
        if prop_class.startswith("u-"):
            return parse_u(target, base_url=ctx.base_url)  # pragma: no cover
        if prop_class.startswith("dt-"):
            dt = parse_dt(target, default_date=default_date)
            if dt.date:
                default_date = dt.date
            return dt.value
        if prop_class.startswith("e-"):
            return parse_e(
                target, base_url=ctx.base_url, root_lang=root_lang, document_lang=ctx.document_lang
            )
        return ""  # pragma: no cover

    def embedded_value(prop_class: str, embedded_item: Mf2Item, target: Element) -> PropertyValue:
        props_obj = embedded_item.get("properties")
        if not isinstance(props_obj, dict):
            return simple_value(prop_class, target)  # pragma: no cover

        def descendant_name_class_info(root: Element) -> tuple[bool, bool]:
            """Return (has_p_name, has_any_typed_name)."""
            has_p_name = False
            has_any_typed_name = False
            name_tokens = {"p-name", "u-name", "dt-name", "e-name"}

            stack: list[Element] = list(iter_child_elements(root))
            while stack:
                cur = stack.pop()
                pcs = property_classes(cur)
                if pcs:
                    for pc in pcs:
                        if pc == "p-name":
                            has_p_name = True
                            has_any_typed_name = True
                            break
                        if pc in name_tokens:
                            has_any_typed_name = True
                    if has_p_name and has_any_typed_name:
                        return True, True
                if is_microformat_root(cur):
                    continue
                stack.extend(iter_child_elements(cur))
            return has_p_name, has_any_typed_name

        if prop_class.startswith("u-"):
            found_url = False
            for key in ("url", "uid"):
                vals = props_obj.get(key)
                if not isinstance(vals, list) or not vals:
                    continue
                found_url = True
                candidate = vals[0]
                url = candidate if isinstance(candidate, str) else str(candidate.get("value", ""))  # type: ignore[union-attr]
                if url.startswith(("http://", "https://")):
                    return candidate
            if found_url:
                # If we have a URL property but it's not an absolute URL, fall back to plain text.
                return parse_p(target, base_url=ctx.base_url)
            # Otherwise, parse the `u-*` value from the element itself (URL join behavior).
            return parse_u(target, base_url=ctx.base_url)

        if prop_class.startswith("p-"):
            vals = props_obj.get("name")
            if (
                isinstance(vals, list)
                and vals
                and isinstance(vals[0], str)
                and not vals[0].startswith(("http://", "https://"))
            ):
                has_p_name, has_any_typed_name = descendant_name_class_info(target)
                # Favor the embedded `p-name` value; otherwise only use implied name.
                if has_p_name or not has_any_typed_name:
                    return vals[0]
            return parse_p(target, base_url=ctx.base_url)

        return simple_value(prop_class, target)

    def handle_property_class(prop_class: str, target: Element) -> None:
        nonlocal default_date
        nonlocal has_p, has_u, has_e
        if prop_class.startswith("p-"):
            has_p = True
            add_prop(prop_class[2:], parse_p(target, base_url=ctx.base_url))
        elif prop_class.startswith("u-"):
            has_u = True
            add_prop(prop_class[2:], parse_u(target, base_url=ctx.base_url))
        elif prop_class.startswith("dt-"):
            dt = parse_dt(target, default_date=default_date)
            add_prop(prop_class[3:], dt.value)
            if dt.date:
                default_date = dt.date
        elif prop_class.startswith("e-"):
            has_e = True
            add_prop(
                prop_class[2:],
                parse_e(
                    target,
                    base_url=ctx.base_url,
                    root_lang=root_lang,
                    document_lang=ctx.document_lang,
                ),
            )
        else:  # pragma: no cover
            return

    def walk(node: Element, *, is_root: bool) -> None:
        nonlocal has_e, has_nested_microformat, has_p, has_u
        if not is_root and is_microformat_root(node):
            has_nested_microformat = True
            nested = _parse_item(
                node,
                ctx,
                parent_lang=root_lang,
                ignore_root_property_classes=frozenset(property_classes(node))
                if _is_property_for_parent(node)
                else frozenset(),
            )
            if _is_property_for_parent(node):
                for pc in property_classes(node):
                    if pc.startswith("p-"):
                        has_p = True
                    elif pc.startswith("u-"):
                        has_u = True
                    elif pc.startswith("e-"):
                        has_e = True
                    name = pc.split("-", 1)[1]
                    embedded = cast(Mf2Item, dict(nested))
                    val = embedded_value(pc, nested, node)
                    if pc.startswith("e-") and isinstance(val, dict):
                        e_val = cast(EValue, val)
                        embedded["value"] = e_val["value"]
                        embedded["html"] = e_val["html"]
                        if "lang" in e_val:
                            embedded["lang"] = e_val["lang"]
                    else:
                        embedded["value"] = val
                    add_prop(name, embedded)
            else:
                children.append(nested)
            return

        pcs = property_classes(node)
        if is_root and ignore_root_property_classes:
            pcs = [pc for pc in pcs if pc not in ignore_root_property_classes]
        for pc in pcs:
            handle_property_class(pc, node)

        for child in iter_child_elements(node):
            walk(child, is_root=False)

    walk(el, is_root=True)

    # Apply implied properties if missing.
    if "name" not in props and not has_p and not has_e and not has_nested_microformat:
        props["name"].append(implied_name(el, ctx.base_url))
    if "photo" not in props and not has_u and not has_nested_microformat:
        photo = implied_photo(el, ctx.base_url)
        if photo is not None:
            props["photo"].append(photo)
    if "url" not in props and not has_u and not has_nested_microformat:
        url = implied_url(el, ctx.base_url)
        if url is not None:
            props["url"].append(url)

    item["properties"] = dict(props)
    if children:
        item["children"] = children
    return item


def parse(
    html: HtmlInput | None,
    *,
    base_url: str | None = None,
    url: str | None = None,
) -> Mf2Document:
    """Parse Microformats2 JSON from HTML or a JustHTML document.

    Returns a dict containing `items`, `rels`, and `rel-urls`.

    Args:
        html: HTML markup, a JustHTML instance, or a JustHTML root node.
        base_url: Base URL for resolving relative URLs. Prefer this parameter.
        url: Deprecated alias for `base_url`.
    """
    if base_url is not None and url is not None and base_url != url:
        msg = "Provide only one of `base_url` or `url`."
        raise ValueError(msg)
    if base_url is None:
        base_url = url

    if isinstance(html, JustHTML):
        doc_root = cast(HasDom, html.root)
    elif html is None or isinstance(html, str | bytes | bytearray | memoryview):
        doc_root = cast(HasDom, JustHTML(html).root)
    else:
        doc_root = cast(HasDom, html)

    base_url = _discover_base_url(doc_root, base_url=base_url)
    document_lang = _first_lang(doc_root)
    ctx = _ParseContext(base_url=base_url, document_lang=document_lang)

    rels, rel_urls = _parse_rels(doc_root, base_url=base_url)
    items = [
        _parse_item(root, ctx, parent_lang=document_lang) for root in _top_level_roots(doc_root)
    ]
    return {"items": items, "rels": rels, "rel-urls": rel_urls}


async def parse_async(
    html: HtmlInput | None,
    *,
    base_url: str | None = None,
    url: str | None = None,
) -> Mf2Document:
    return await asyncio.to_thread(parse, html, base_url=base_url, url=url)

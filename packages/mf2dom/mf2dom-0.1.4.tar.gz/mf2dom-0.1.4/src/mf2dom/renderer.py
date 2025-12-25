"""Microformats2 renderer.

Renders mf2 JSON back into semantic HTML in a deterministic way such that:
HTML1 -> JSON -> HTML2 -> JSON -> HTML2

The output uses semantic HTML5 elements that render beautifully with
classless CSS frameworks like PicoCSS.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from typing import TYPE_CHECKING, TypeGuard, cast

if TYPE_CHECKING:  # pragma: no cover
    from .types import EValue, Mf2Document, Mf2Item, RelUrl, UrlObject


# Semantic element mapping for h-* root types
_SEMANTIC_ROOT_ELEMENTS: dict[str, str] = {
    "h-entry": "article",
    "h-feed": "section",
    "h-event": "article",
    "h-product": "article",
    "h-recipe": "article",
    "h-review": "article",
    "h-resume": "article",
    "h-adr": "address",
    "h-cite": "blockquote",
    "h-geo": "data",
}

# Semantic element mapping for properties
_SEMANTIC_PROPERTY_ELEMENTS: dict[str, str] = {
    # Address components use address element
    "p-adr": "address",
    "p-street-address": "span",
    "p-extended-address": "span",
    "p-locality": "span",
    "p-region": "span",
    "p-postal-code": "span",
    "p-country-name": "span",
    # Name properties use strong for emphasis
    "p-name": "strong",
    # Paragraph-like properties
    "p-summary": "p",
    "p-note": "p",
    "p-content": "p",
    "p-description": "p",
    # Author info
    "p-author": "span",
}

# Properties that are typically URLs (should render as <a>)
_URL_PROPERTIES: frozenset[str] = frozenset(
    {
        "url",
        "uid",
        "photo",
        "logo",
        "video",
        "audio",
        "syndication",
        "in-reply-to",
        "like-of",
        "repost-of",
        "bookmark-of",
        "tag-of",
        "location",
    }
)

# Properties that are emails (should render as <a href="mailto:">)
_EMAIL_PROPERTIES: frozenset[str] = frozenset({"email"})

# Properties that are telephone numbers (should render as <a href="tel:">)
_TEL_PROPERTIES: frozenset[str] = frozenset({"tel"})

# Properties that are typically datetimes (should render as <time>)
_DATETIME_PROPERTIES: frozenset[str] = frozenset(
    {
        "published",
        "updated",
        "start",
        "end",
        "duration",
        "bday",
        "anniversary",
        "rev",
    }
)

# Semantic property ordering based on microformats.org wiki
# Properties are grouped by semantic meaning for good display across types:
# 1. Visual identity (photo, logo)
# 2. Name/identity
# 3. Author (for h-entry)
# 4. Description/content
# 5. Dates (important for h-entry, h-event)
# 6. Location (for h-event, h-card)
# 7. URLs and links
# 8. Contact info (email, tel)
# 9. Address details
# 10. Organization/role
# 11. Categories and other metadata
_PROPERTY_ORDER: list[str] = [
    # Visual identity first
    "photo",
    "logo",
    "featured",
    # Name properties
    "name",
    "honorific-prefix",
    "given-name",
    "additional-name",
    "family-name",
    "sort-string",
    "honorific-suffix",
    "nickname",
    # Author (important for h-entry)
    "author",
    # Description/content
    "summary",
    "note",
    "content",
    "description",
    # Dates (prominent for h-entry, h-event)
    "published",
    "updated",
    "start",
    "end",
    "duration",
    "bday",
    "anniversary",
    "rev",
    # Location (for h-event)
    "location",
    # URLs and links
    "url",
    "uid",
    "syndication",
    "in-reply-to",
    "like-of",
    "repost-of",
    "bookmark-of",
    # Contact info
    "email",
    "tel",
    "impp",
    # Address details
    "adr",
    "geo",
    "latitude",
    "longitude",
    "altitude",
    "street-address",
    "extended-address",
    "locality",
    "region",
    "postal-code",
    "country-name",
    "label",
    # Organization/role
    "org",
    "job-title",
    "role",
    # Categories and metadata
    "category",
    "rsvp",
    "attendee",
    "key",
    "sex",
    "gender-identity",
]


def _property_sort_key(prop: str) -> tuple[int, str]:
    """Return a sort key for property ordering."""
    try:
        return (_PROPERTY_ORDER.index(prop), prop)
    except ValueError:
        return (len(_PROPERTY_ORDER), prop)


def _get_semantic_element(types: Sequence[str]) -> str:
    """Determine the semantic HTML element based on microformat types."""
    for t in types:
        if t in _SEMANTIC_ROOT_ELEMENTS:
            return _SEMANTIC_ROOT_ELEMENTS[t]
    return "div"


def _get_property_element(prop: str, prefix: str) -> str:
    """Determine the semantic HTML element for a property."""
    full_prop = f"{prefix}-{prop}"
    return _SEMANTIC_PROPERTY_ELEMENTS.get(full_prop, "span")


def _is_mf2_item(value: object) -> TypeGuard[Mf2Item]:
    return isinstance(value, dict) and "type" in value and "properties" in value


def _class_attr(classes: Sequence[str]) -> str:
    cls = " ".join(c for c in classes if c)
    return f' class="{escape(cls, quote=True)}"' if cls else ""


def _id_attr(value: object) -> str:
    return f' id="{escape(str(value), quote=True)}"' if isinstance(value, str) and value else ""


def _value_vcp_node(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict) and "value" in value:
        value = value["value"]  # type: ignore[literal-required]
    if not isinstance(value, str):
        value = str(value)
    return f'<data class="value" value="{escape(value, quote=True)}"></data>'


def _rel_attr(url: str, rel_urls: dict[str, RelUrl] | None) -> str:
    """Generate rel attribute if URL has associated rels."""
    if not rel_urls or url not in rel_urls:
        return ""
    rels = rel_urls[url].get("rels", [])
    if not rels:
        return ""
    return f' rel="{escape(" ".join(rels), quote=True)}"'


def _render_text_property(
    prop: str,
    value: str,
    rel_urls: dict[str, RelUrl] | None = None,
) -> str:
    # Use semantic elements based on property type
    if prop in _URL_PROPERTIES and value.startswith(("http://", "https://", "/")):
        cls = _class_attr([f"u-{prop}"])
        href = escape(value, quote=True)
        rel = _rel_attr(value, rel_urls)
        return f'<a{cls} href="{href}"{rel}>{escape(value)}</a>'
    if prop in _EMAIL_PROPERTIES:
        cls = _class_attr([f"u-{prop}"])
        href = escape(value if value.startswith("mailto:") else f"mailto:{value}", quote=True)
        return f'<a{cls} href="{href}">{escape(value)}</a>'
    if prop in _TEL_PROPERTIES:
        cls = _class_attr([f"p-{prop}"])
        href = escape(value if value.startswith("tel:") else f"tel:{value}", quote=True)
        return f'<a{cls} href="{href}">{escape(value)}</a>'
    if prop in _DATETIME_PROPERTIES:
        cls = _class_attr([f"dt-{prop}"])
        dt = escape(value, quote=True)
        return f'<time{cls} datetime="{dt}">{escape(value)}</time>'
    tag = _get_property_element(prop, "p")
    return f"<{tag}{_class_attr([f'p-{prop}'])}>{escape(value)}</{tag}>"


def _render_string_property(
    prefix: str,
    prop: str,
    value: str,
    rel_urls: dict[str, RelUrl] | None = None,
) -> str:
    if prefix == "dt":
        return f"<time{_class_attr([f'dt-{prop}'])}>{escape(value)}</time>"
    if prefix == "u":
        rel = _rel_attr(value, rel_urls)
        return f'<a{_class_attr([f"u-{prop}"])} href="{escape(value, quote=True)}"{rel}></a>'
    if prefix == "e":
        return f"<div{_class_attr([f'e-{prop}'])}>{escape(value)}</div>"
    return _render_text_property(prop, value, rel_urls)


def _render_e_property(prop: str, value: EValue) -> str:
    html = value.get("html")
    inner = html if isinstance(html, str) else escape(str(value.get("value", "")))
    return f"<div{_class_attr([f'e-{prop}'])}>{inner}</div>"


def _render_u_object_property(prop: str, value: UrlObject) -> str:
    url = value.get("value", "")
    alt = value.get("alt")
    attrs = [f"u-{prop}"]
    alt_attr = ""
    if alt is not None:
        alt_attr = f' alt="{escape(str(alt), quote=True)}"'
    srcset = value.get("srcset")
    srcset_attr = ""
    if isinstance(srcset, dict) and srcset:
        # Stable ordering by key.
        parts = [f"{src} {key}" for key, src in sorted(srcset.items())]
        srcset_attr = f' srcset="{escape(", ".join(parts), quote=True)}"'
    return f'<img{_class_attr(attrs)} src="{escape(url, quote=True)}"{alt_attr}{srcset_attr}>'


def _embedded_property_prefix(embedded: Mf2Item) -> str:
    if isinstance(embedded.get("html"), str):
        return "e"
    value = embedded.get("value")
    if isinstance(value, Mapping):
        return "u"
    return "p"


def _render_item(
    item: Mf2Item,
    *,
    extra_classes: Sequence[str] = (),
    as_property: bool = False,
    property_prefix: str | None = None,
    rel_urls: dict[str, RelUrl] | None = None,
) -> str:
    classes: list[str] = []
    classes.extend(str(c) for c in extra_classes if c)
    item_types = item.get("type", [])
    classes.extend(str(t) for t in item_types)
    props = item.get("properties", {})
    children = item.get("children", [])

    # Use semantic element based on microformat type
    tag = _get_semantic_element(item_types)
    out: list[str] = [f"<{tag}{_id_attr(item.get('id'))}{_class_attr(classes)}>"]

    if (
        as_property
        and property_prefix in {"p", "dt"}
        and "value" in item
        and not isinstance(item.get("value"), Mapping)
    ):
        out.append(_value_vcp_node(item.get("value")))

    embedded_value = item.get("value") if as_property else None

    if as_property and property_prefix == "e":
        html = item.get("html")
        if isinstance(html, str):
            out.append(html)
            out.append(f"</{tag}>")
            return "".join(out)

    for prop in sorted(props.keys(), key=_property_sort_key):
        for v in props[prop]:
            if _is_mf2_item(v):
                # Embedded microformat.
                item = cast("Mf2Item", v)
                prefix = _embedded_property_prefix(item)
                out.append(
                    _render_item(
                        item,
                        extra_classes=[f"{prefix}-{prop}"],
                        as_property=True,
                        property_prefix=prefix,
                        rel_urls=rel_urls,
                    ),
                )
            elif isinstance(v, dict) and "html" in v:
                out.append(_render_e_property(prop, v))  # type: ignore[arg-type]
            elif isinstance(v, dict) and ("alt" in v or "srcset" in v) and "value" in v:
                out.append(_render_u_object_property(prop, v))  # type: ignore[arg-type]
            # If this item is itself embedded as a property, prefer dt-* for `name`
            # when its representative value differs from its `properties.name[0]`.
            elif (
                as_property
                and property_prefix == "p"
                and prop == "name"
                and isinstance(embedded_value, str)
                and isinstance(v, str)
                and v != embedded_value
                and not v.startswith(("http://", "https://"))
            ):
                out.append(_render_string_property("dt", prop, v, rel_urls))
            else:
                out.append(_render_text_property(prop, str(v), rel_urls))

    out.extend(_render_item(child, rel_urls=rel_urls) for child in children)

    out.append(f"</{tag}>")
    return "".join(out)


def render(doc: Mf2Document) -> str:
    items = doc["items"]
    rel_urls = doc["rel-urls"]

    out: list[str] = ["<main>"]

    out.extend(_render_item(item, rel_urls=rel_urls) for item in items)

    # Render rels in a semantic nav element, in stable order by URL.
    if rel_urls:
        out.append("<nav>")
        for url, info in sorted(rel_urls.items(), key=lambda kv: str(kv[0])):
            rels = info.get("rels", [])
            rel_attr = f' rel="{escape(" ".join(rels), quote=True)}"' if rels else ""
            text = info.get("text", url)
            out.append(f'<a href="{escape(url, quote=True)}"{rel_attr}>{escape(text)}</a>')
        out.append("</nav>")

    out.append("</main>")
    return "".join(out)

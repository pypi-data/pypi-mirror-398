"""Microformats2 renderer.

Renders mf2 JSON back into semantic HTML in a deterministic way such that:
HTML1 -> JSON -> HTML2 -> JSON -> HTML2

The output uses semantic HTML5 elements that render beautifully with
classless CSS frameworks like PicoCSS.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, TypeGuard, cast

from justhtml import JustHTML
from justhtml.node import SimpleDomNode

from .types import Mf2Document, Mf2Item

if TYPE_CHECKING:  # pragma: no cover
    from .types import EValue, RelUrl, UrlObject


def _el(tag: str, attrs: dict[str, str | None] | None = None) -> SimpleDomNode:
    """Create an element with optional attributes."""
    node = SimpleDomNode(tag)
    node.attrs = attrs if attrs is not None else {}
    return node


def _text(data: str) -> SimpleDomNode:
    """Create a text node."""
    node = SimpleDomNode("#text")
    node.data = data
    return node


def _parse_html_fragment(html: str) -> list[SimpleDomNode]:
    """Parse HTML and return the body's children (cloned)."""
    doc = JustHTML(f"<body>{html}</body>")
    html_el = doc.root.children[0]  # #document > html  # type: ignore[index]
    body = html_el.children[1]  # html > body  # type: ignore[union-attr]
    return [child.clone_node(deep=True) for child in body.children]


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


def _get_render_category(prop: str, value: str) -> str:
    """Return a category string for grouping properties with the same value.

    Properties with the same value and category can be merged into a single element.
    """
    if prop in _URL_PROPERTIES and value.startswith(("http://", "https://", "/")):
        return "url"
    if prop in _EMAIL_PROPERTIES:
        return "email"
    if prop in _TEL_PROPERTIES:
        return "tel"
    if prop in _DATETIME_PROPERTIES:
        return "datetime"
    return f"text:{prop}"  # Different text properties use different elements


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


def _class_value(classes: Sequence[str]) -> str | None:
    """Return class attribute value or None if empty."""
    cls = " ".join(c for c in classes if c)
    return cls if cls else None


def _value_vcp_node(value: object) -> SimpleDomNode | None:
    """Create a VCP data node for the value."""
    if value is None:
        return None
    if isinstance(value, dict) and "value" in value:
        value = value["value"]  # type: ignore[literal-required]
    if not isinstance(value, str):
        value = str(value)
    return _el("data", {"class": "value", "value": value})


def _get_rels(url: str, rel_urls: dict[str, RelUrl] | None) -> str | None:
    """Get rel attribute value if URL has associated rels."""
    if not rel_urls or url not in rel_urls:
        return None
    rels = rel_urls[url].get("rels", [])
    if not rels:
        return None
    return " ".join(rels)


def _render_text_property(
    props: Sequence[str],
    value: str,
    rel_urls: dict[str, RelUrl] | None = None,
) -> SimpleDomNode:
    """Render one or more properties with the same value as a single element."""
    # Use the first property to determine rendering style (all should be same category)
    prop = props[0]
    # Photo/logo should render as <img>, not <a>
    if prop in {"photo", "logo"}:
        cls = _class_value([f"u-{p}" for p in props])
        return _el("img", {"class": cls, "src": value})
    # Video should render as <video>, not <a>
    if prop == "video":
        cls = _class_value([f"u-{p}" for p in props])
        return _el("video", {"class": cls, "src": value})
    # Audio should render as <audio>, not <a>
    if prop == "audio":
        cls = _class_value([f"u-{p}" for p in props])
        return _el("audio", {"class": cls, "src": value})
    # Use semantic elements based on property type
    if prop in _URL_PROPERTIES and value.startswith(("http://", "https://", "/")):
        cls = _class_value([f"u-{p}" for p in props])
        rel = _get_rels(value, rel_urls)
        attrs: dict[str, str | None] = {"class": cls, "href": value}
        if rel:
            attrs["rel"] = rel
        el = _el("a", attrs)
        el.append_child(_text(value))
        return el
    if prop in _EMAIL_PROPERTIES:
        cls = _class_value([f"u-{p}" for p in props])
        href = value if value.startswith("mailto:") else f"mailto:{value}"
        el = _el("a", {"class": cls, "href": href})
        el.append_child(_text(value))
        return el
    if prop in _TEL_PROPERTIES:
        cls = _class_value([f"p-{p}" for p in props])
        href = value if value.startswith("tel:") else f"tel:{value}"
        el = _el("a", {"class": cls, "href": href})
        el.append_child(_text(value))
        return el
    if prop in _DATETIME_PROPERTIES:
        cls = _class_value([f"dt-{p}" for p in props])
        el = _el("time", {"class": cls, "datetime": value})
        el.append_child(_text(value))
        return el
    tag = _get_property_element(prop, "p")
    cls = _class_value([f"p-{p}" for p in props])
    el = _el(tag, {"class": cls})
    el.append_child(_text(value))
    return el


def _render_string_property(
    prefix: str,
    props: Sequence[str],
    value: str,
    rel_urls: dict[str, RelUrl] | None = None,
) -> SimpleDomNode:
    """Render one or more properties with the same value as a single element."""
    if prefix == "dt":
        cls = _class_value([f"dt-{p}" for p in props])
        el = _el("time", {"class": cls})
        el.append_child(_text(value))
        return el
    if prefix == "u":
        rel = _get_rels(value, rel_urls)
        cls = _class_value([f"u-{p}" for p in props])
        attrs: dict[str, str | None] = {"class": cls, "href": value}
        if rel:
            attrs["rel"] = rel
        return _el("a", attrs)
    if prefix == "e":
        cls = _class_value([f"e-{p}" for p in props])
        el = _el("div", {"class": cls})
        el.append_child(_text(value))
        return el
    return _render_text_property(props, value, rel_urls)


def _render_e_property(prop: str, value: EValue) -> SimpleDomNode:
    """Render an e-* property with HTML content."""
    html = value.get("html")
    cls = _class_value([f"e-{prop}"])
    el = _el("div", {"class": cls})
    if isinstance(html, str):
        # Parse the HTML and append the children
        for child in _parse_html_fragment(html):
            el.append_child(child)
    else:
        el.append_child(_text(str(value.get("value", ""))))
    return el


def _render_u_object_property(prop: str, value: UrlObject) -> SimpleDomNode:
    """Render a u-* property with object value (img with alt/srcset)."""
    url = value.get("value", "")
    alt = value.get("alt")
    cls = _class_value([f"u-{prop}"])
    attrs: dict[str, str | None] = {"class": cls, "src": url}
    if alt is not None:
        attrs["alt"] = str(alt)
    srcset = value.get("srcset")
    if isinstance(srcset, dict) and srcset:
        # Stable ordering by key.
        parts = [f"{src} {key}" for key, src in sorted(srcset.items())]
        attrs["srcset"] = ", ".join(parts)
    return _el("img", attrs)


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
) -> SimpleDomNode:
    classes: list[str] = []
    classes.extend(str(c) for c in extra_classes if c)
    item_types = item.get("type", [])
    classes.extend(str(t) for t in item_types)
    props = item.get("properties", {})
    children = item.get("children", [])

    # Use semantic element based on microformat type
    tag = _get_semantic_element(item_types)
    attrs: dict[str, str | None] = {}
    item_id = item.get("id")
    if isinstance(item_id, str) and item_id:
        attrs["id"] = item_id
    cls = _class_value(classes)
    if cls:
        attrs["class"] = cls
    el = _el(tag, attrs)

    if (
        as_property
        and property_prefix in {"p", "dt"}
        and "value" in item
        and not isinstance(item.get("value"), Mapping)
    ):
        vcp_node = _value_vcp_node(item.get("value"))
        if vcp_node:
            el.append_child(vcp_node)

    embedded_value = item.get("value") if as_property else None

    if as_property and property_prefix == "e":
        html = item.get("html")
        if isinstance(html, str):
            for child in _parse_html_fragment(html):
                el.append_child(child)
            return el

    # Group string properties by (value, category) for combined rendering.
    # Key: (value, category), Value: list of property names
    value_groups: dict[tuple[str, str], list[str]] = {}
    # Track which (value, category) pairs have been rendered
    rendered_groups: set[tuple[str, str]] = set()

    for prop in sorted(props.keys(), key=_property_sort_key):
        for v in props[prop]:
            if _is_mf2_item(v):
                # Embedded microformat - render immediately.
                embedded = cast(Mf2Item, v)
                prefix = _embedded_property_prefix(embedded)
                el.append_child(
                    _render_item(
                        embedded,
                        extra_classes=[f"{prefix}-{prop}"],
                        as_property=True,
                        property_prefix=prefix,
                        rel_urls=rel_urls,
                    ),
                )
            elif isinstance(v, dict) and "html" in v:
                el.append_child(_render_e_property(prop, v))  # type: ignore[arg-type]
            elif isinstance(v, dict) and ("alt" in v or "srcset" in v) and "value" in v:
                el.append_child(_render_u_object_property(prop, v))  # type: ignore[arg-type]
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
                el.append_child(_render_string_property("dt", [prop], v, rel_urls))
            elif isinstance(v, str):
                # Group string values by (value, category).
                category = _get_render_category(prop, v)
                key = (v, category)
                if key not in value_groups:
                    value_groups[key] = []
                value_groups[key].append(prop)
                # Render on first occurrence, which maintains property order.
                if key not in rendered_groups:
                    rendered_groups.add(key)
                    # Collect all props with this value across all properties.
                    group_props = []
                    for p in sorted(props.keys(), key=_property_sort_key):
                        for pv in props[p]:
                            if (
                                isinstance(pv, str)
                                and pv == v
                                and _get_render_category(p, pv) == category
                                and p not in group_props
                            ):
                                group_props.append(p)
                    el.append_child(_render_text_property(group_props, v, rel_urls))
            else:
                el.append_child(_render_text_property([prop], str(v), rel_urls))

    for child in children:
        el.append_child(_render_item(child, rel_urls=rel_urls))

    return el


def render(
    doc: Mf2Document,
    *,
    pretty: bool = False,
    indent_size: int = 2,
) -> str:
    """Render an mf2 document to HTML.

    Args:
        doc: The mf2 document to render.
        pretty: If True, output nicely indented HTML. Default is False (minified).
        indent_size: Number of spaces for each indentation level when pretty=True.
            Default is 2.

    Returns:
        The rendered HTML string.
    """
    items = doc["items"]
    rel_urls = doc["rel-urls"]

    main = _el("main")

    for item in items:
        main.append_child(_render_item(item, rel_urls=rel_urls))

    # Render rels in a semantic nav element, in stable order by URL.
    if rel_urls:
        nav = _el("nav")
        for url, info in sorted(rel_urls.items(), key=lambda kv: str(kv[0])):
            rels = info.get("rels", [])
            attrs: dict[str, str | None] = {"href": url}
            if rels:
                attrs["rel"] = " ".join(rels)
            a = _el("a", attrs)
            text = info.get("text", url)
            a.append_child(_text(text))
            nav.append_child(a)
        main.append_child(nav)

    return main.to_html(pretty=pretty, indent_size=indent_size)

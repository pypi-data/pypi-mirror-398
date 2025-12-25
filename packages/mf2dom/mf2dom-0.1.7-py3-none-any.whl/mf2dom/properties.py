"""Property parsing for mf2 (`p-`, `u-`, `dt-`, `e-`) and microformat detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from justhtml.constants import VOID_ELEMENTS

from .classes import has_root_class
from .classes import property_classes as mf2_property_classes
from .classes import root_types as mf2_root_types
from .dom import (
    Element,
    get_attr,
    get_classes,
    is_element,
    iter_preorder_elements,
)
from .text import text_content
from .urls import parse_srcset, try_urljoin
from .vcp import _DATE_RE, _DATETIME_RE_COMPILED, _TIME_RE, normalize_datetime
from .vcp import datetime as vcp_datetime
from .vcp import text as vcp_text

if TYPE_CHECKING:  # pragma: no cover
    from .types import EValue, UrlObject, UrlValue


@dataclass(slots=True)
class DtResult:
    value: str
    date: str | None


def parse_p(el: Element, *, base_url: str | None) -> str:
    if (v := vcp_text(el)) is not None:
        return v

    title = get_attr(el, "title")
    tag = el.name.lower()
    if title is not None and tag in {"abbr", "link"}:
        return title

    value = get_attr(el, "value")
    if value is not None and tag in {"data", "input"}:
        return value

    alt = get_attr(el, "alt")
    if alt is not None and tag in {"img", "area"}:
        return alt

    return text_content(el, replace_img=True, img_to_src=False, base_url=base_url).strip()


def _img_value(img: Element, base_url: str | None) -> UrlValue | None:
    src = get_attr(img, "src")
    if src is None:
        return None
    src_abs = try_urljoin(base_url, src) or src
    alt = get_attr(img, "alt")
    srcset = get_attr(img, "srcset")
    if alt is not None or srcset:
        out: UrlObject = {"value": src_abs}
        if alt is not None:
            out["alt"] = alt
        if srcset:
            out["srcset"] = parse_srcset(srcset, base_url)
        return out
    return src_abs


def parse_u(el: Element, *, base_url: str | None) -> UrlValue:
    tag = el.name.lower()

    href = get_attr(el, "href")
    if href is not None and tag in {"a", "area", "link"}:
        return try_urljoin(base_url, href) or href

    if tag == "img":
        img = _img_value(el, base_url)
        if img is not None:
            return img

    src = get_attr(el, "src")
    if src is not None and tag in {"audio", "video", "source", "iframe"}:
        return try_urljoin(base_url, src) or src

    poster = get_attr(el, "poster")
    if poster is not None and tag == "video":
        return try_urljoin(base_url, poster) or poster

    data = get_attr(el, "data")
    if data is not None and tag == "object":
        return try_urljoin(base_url, data) or data

    v = vcp_text(el)
    if v is not None:
        return try_urljoin(base_url, v) or v

    if tag == "abbr":
        title = get_attr(el, "title")
        if title is not None:
            return try_urljoin(base_url, title) or title

    value = get_attr(el, "value")
    if value is not None and tag in {"data", "input"}:
        return try_urljoin(base_url, value) or value

    txt = text_content(el).strip()
    return try_urljoin(base_url, txt) or txt


_TIME_ONLY_RE = re.compile(_TIME_RE + "$")
_DATETIME_RE = _DATETIME_RE_COMPILED


def parse_dt(el: Element, *, default_date: str | None) -> DtResult:
    v = vcp_datetime(el, default_date)
    if v is not None:
        return DtResult(value=v[0], date=v[1])

    tag = el.name.lower()
    prop_value: str
    from_attr = False
    if tag in {"time", "ins", "del"}:
        dt = get_attr(el, "datetime")
        if dt is not None:
            prop_value = dt
            from_attr = True
        else:
            prop_value = text_content(el)
    elif tag == "abbr":
        title = get_attr(el, "title")
        if title is not None:
            prop_value = title
            from_attr = True
        else:
            prop_value = text_content(el)
    elif tag in {"data", "input"}:
        value = get_attr(el, "value")
        if value is not None:
            prop_value = value
            from_attr = True
        else:
            prop_value = text_content(el)
    else:
        prop_value = text_content(el)

    stripped = prop_value.strip()

    time_match = _TIME_ONLY_RE.match(stripped)
    if time_match and default_date:
        combined = f"{default_date} {stripped}"
        match = _DATETIME_RE.match(combined)
        return DtResult(value=normalize_datetime(combined, match=match), date=default_date)

    match = _DATETIME_RE.match(stripped)
    if match:
        normalized = normalize_datetime(stripped, match=match)
        # If normalization didn't change (no AM/PM), preserve original attribute spacing.
        if from_attr and normalized == stripped:
            return DtResult(value=prop_value, date=match.group("date"))
        return DtResult(value=normalized, date=match.group("date"))
    date_match = re.match(_DATE_RE + "$", stripped)
    return DtResult(
        value=(prop_value if from_attr else stripped),
        date=(date_match.group(0) if date_match else None),
    )


_URL_ATTRS_IN_E = ("href", "src", "cite", "data", "poster")


def _inner_html(el: Element) -> str:
    return "".join(_serialize_node(child) for child in el.children or [])


def _escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr_value(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;")


def _serialize_element(el: Element) -> str:
    name = el.name
    parts: list[str] = [f"<{name}"]
    for key, value in (el.attrs or {}).items():
        if value is None:
            parts.append(f" {key}")
        else:
            parts.append(f' {key}="{_escape_attr_value(str(value))}"')
    parts.append(">")
    start = "".join(parts)
    if name.lower() in VOID_ELEMENTS:
        return start
    inner = "".join(_serialize_node(child) for child in el.children or [])
    return f"{start}{inner}</{name}>"


def _serialize_node(node: Any) -> str:
    name = getattr(node, "name", "")
    if name == "#text":
        data = getattr(node, "data", None)
        return _escape_text(str(data)) if data is not None else ""
    if name == "#comment":
        data = getattr(node, "data", "") or ""
        return f"<!--{data}-->"
    if name in {"!doctype", "#document", "#document-fragment"}:
        return "".join(_serialize_node(child) for child in getattr(node, "children", None) or [])
    if name.lower() == "template":
        return ""
    if is_element(node):
        return _serialize_element(node)
    return ""


def parse_e(
    el: Element,
    *,
    base_url: str | None,
    root_lang: str | None,
    document_lang: str | None,
) -> EValue:
    clone = el.clone_node(deep=True)  # type: ignore[attr-defined]
    for tag in iter_preorder_elements(clone):
        for attr in _URL_ATTRS_IN_E:
            val = get_attr(tag, attr)
            if val is not None:
                tag.attrs[attr] = try_urljoin(base_url, val)

    out: EValue = {
        "value": text_content(el, replace_img=True, base_url=base_url).strip(),
        "html": "",
    }

    lang = get_attr(el, "lang") or root_lang or document_lang
    if lang:
        out["lang"] = lang

    out["html"] = _inner_html(clone).strip()
    return out


def is_microformat_root(el: Element) -> bool:
    return has_root_class(get_classes(el))


def root_types(el: Element) -> list[str]:
    return mf2_root_types(get_classes(el))


def property_classes(el: Element) -> list[str]:
    return mf2_property_classes(get_classes(el))

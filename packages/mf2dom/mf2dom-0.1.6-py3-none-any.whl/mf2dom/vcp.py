"""Value Class Pattern (VCP) parsing.

Implements the mf2 Value Class Pattern for `p-*`, `u-*`, and `dt-*` properties.
See: https://microformats.org/wiki/value-class-pattern
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .classes import has_root_class, is_valid_property_class
from .dom import (
    Element,
    get_attr,
    get_classes,
    iter_child_elements,
)
from .text import text_content

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator

_DATE_RE = r"(\d{4}-\d{2}-\d{2})|(\d{4}-\d{3})"
_SEC_RE = r"(:(?P<second>\d{2})(\.\d+)?)"
_RAWTIME_RE = rf"(?P<hour>\d{{1,2}})(:(?P<minute>\d{{2}}){_SEC_RE}?)?"
_AMPM_RE = r"am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\."
_TIMEZONE_RE = r"Z|[+-]\d{1,2}:?\d{2}?"
_TIME_RE = rf"(?P<rawtime>{_RAWTIME_RE})( ?(?P<ampm>{_AMPM_RE}))?( ?(?P<tz>{_TIMEZONE_RE}))?"
_DATETIME_RE = rf"(?P<date>{_DATE_RE})(?P<separator>[Tt ])(?P<time>{_TIME_RE})"

_TIME_RE_COMPILED = re.compile(_TIME_RE + "$")
_DATE_RE_COMPILED = re.compile(_DATE_RE + "$")
_TZ_ONLY_RE_COMPILED = re.compile(_TIMEZONE_RE + "$")
_DATETIME_RE_COMPILED = re.compile(_DATETIME_RE + "$")

_HOURS_IN_HALF_DAY = 12


def _is_value_node(el: Element) -> bool:
    classes = set(get_classes(el))
    return "value" in classes or "value-title" in classes


def _is_property_node(el: Element) -> bool:
    return any(is_valid_property_class(c) for c in get_classes(el))


def _is_microformat_root(el: Element) -> bool:
    return has_root_class(get_classes(el))


def _iter_value_nodes(root: Element) -> Iterator[Element]:
    # Descendants (not self), in document order, but do not traverse into nested
    # properties or microformats unless the node itself is a value node.
    stack: list[Element] = list(reversed(list(iter_child_elements(root))))
    while stack:
        el = stack.pop()
        if _is_value_node(el):
            yield el
            continue
        if _is_property_node(el) or _is_microformat_root(el):
            continue
        stack.extend(reversed(list(iter_child_elements(el))))


def text(root: Element) -> str | None:
    parts: list[str] = []
    for el in _iter_value_nodes(root):
        classes = set(get_classes(el))
        if "value-title" in classes:
            title = get_attr(el, "title")
            if title is not None:
                parts.append(title)
            continue

        tag = el.name.lower()
        if tag in {"img", "area"}:
            alt = get_attr(el, "alt")
            if alt is not None:
                parts.append(alt)
            else:
                parts.append(text_content(el))
        elif tag in {"data", "input"}:
            val = get_attr(el, "value")
            parts.append(val if val is not None else text_content(el))
        elif tag == "abbr":
            title = get_attr(el, "title")
            parts.append(title if title is not None else text_content(el))
        else:
            parts.append(text_content(el))

    if not parts:
        return None
    return "".join(parts)


def datetime(root: Element, default_date: str | None) -> tuple[str, str | None] | None:
    raw_parts: list[tuple[str, bool]] = []
    for el in _iter_value_nodes(root):
        classes = set(get_classes(el))
        if "value-title" in classes:
            title = get_attr(el, "title")
            if title:
                raw_parts.append((title.strip(), False))
            continue

        tag = el.name.lower()
        if tag in {"img", "area"}:
            alt = get_attr(el, "alt") or text_content(el)
            if alt:
                raw_parts.append((alt.strip(), False))
        elif tag in {"data", "input"}:
            val = get_attr(el, "value") or text_content(el)
            if val:
                raw_parts.append((val.strip(), False))
        elif tag == "abbr":
            title = get_attr(el, "title") or text_content(el)
            if title:
                raw_parts.append((title.strip(), False))
        elif tag in {"del", "ins", "time"}:
            dt = get_attr(el, "datetime") or text_content(el)
            if dt:
                raw_parts.append((dt.strip(), True))
        else:
            txt = text_content(el)
            if txt:
                raw_parts.append((txt.strip(), False))

    if not raw_parts:
        return None

    date_part: str | None = None
    time_part: str | None = None
    time_part_from_time_el = False
    tz_part: str | None = None

    for part, from_time_el in raw_parts:
        dt_match = _DATETIME_RE_COMPILED.match(part)
        if dt_match:
            if date_part is None and time_part is None and tz_part is None:
                normalized = normalize_datetime(part, match=dt_match)
                return normalized, dt_match.group("date")
            continue

        if date_part is None and _DATE_RE_COMPILED.match(part):
            date_part = part
            continue

        time_match = _TIME_RE_COMPILED.match(part)
        if time_part is None and time_match:
            time_part = part
            time_part_from_time_el = from_time_el
            tz_group = time_match.group("tz")
            if tz_part is None and tz_group:
                tz_part = tz_group
            continue

        if tz_part is None and _TZ_ONLY_RE_COMPILED.match(part):
            tz_part = part

    if date_part is None and time_part is None:
        return None
    if date_part is None and time_part is not None:
        date_part = default_date

    value = f"{date_part} {time_part}" if date_part and time_part else date_part or time_part or ""

    if tz_part and time_part and tz_part not in value:
        value += tz_part

    if time_part_from_time_el:
        # In the official test suite, timezones with a colon originating from <time>/<ins>/<del>
        # value nodes are normalized to the compact form (e.g. -08:00 => -0800).
        value = re.sub(r"([+-]\d{1,2}):(\d{2})$", r"\1\2", value)

    match = _DATETIME_RE_COMPILED.match(value)
    if match:
        value = normalize_datetime(value, match=match)
    return value, date_part


def normalize_datetime(dtstr: str, *, match: re.Match[str] | None = None) -> str:
    match = match or _DATETIME_RE_COMPILED.match(dtstr)
    if not match:
        return dtstr

    datestr = match.group("date")
    separator = match.group("separator")
    hour = match.group("hour")
    minute = match.group("minute")
    second = match.group("second")
    ampm = match.group("ampm")
    tz = match.group("tz") or ""

    # Only normalize when AM/PM is present.
    if not ampm:
        return dtstr

    hour_int = int(hour)
    if ampm.lower().startswith("a") and hour_int == _HOURS_IN_HALF_DAY:
        hour_int = 0
    elif ampm.lower().startswith("p") and hour_int < _HOURS_IN_HALF_DAY:
        hour_int += _HOURS_IN_HALF_DAY

    minute_out = minute or "00"
    time_out = f"{hour_int:02d}:{minute_out}"
    if second is not None:
        time_out += f":{second}"

    return f"{datestr}{separator}{time_out}{tz}"

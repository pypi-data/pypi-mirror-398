"""Type definitions for mf2dom.

These TypedDicts model the JSON output defined by the Microformats2 parsing
specification and the official test suite.
"""

from __future__ import annotations

from typing import NotRequired, TypeAlias, TypedDict


class UrlObject(TypedDict):
    value: str
    alt: NotRequired[str]
    srcset: NotRequired[dict[str, str]]


class EValue(TypedDict, total=False):
    value: str
    html: str
    lang: str


PropertyPrimitive: TypeAlias = str
UrlValue: TypeAlias = str | UrlObject


class Mf2Item(TypedDict, total=False):
    type: list[str]
    properties: dict[str, list[PropertyValue]]
    id: str
    children: list[Mf2Item]
    value: PropertyValue
    html: str
    lang: str


PropertyValue: TypeAlias = PropertyPrimitive | UrlObject | EValue | Mf2Item


class RelUrl(TypedDict, total=False):
    rels: list[str]
    text: str
    media: str
    hreflang: str
    type: str
    title: str


Mf2Document = TypedDict(
    "Mf2Document",
    {
        "items": list[Mf2Item],
        "rels": dict[str, list[str]],
        "rel-urls": dict[str, RelUrl],
    },
)

from __future__ import annotations

import asyncio
import importlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from mf2dom.types import Mf2Item

import pytest
from justhtml import JustHTML

from mf2dom.classes import is_valid_mf2_name
from mf2dom.dom import (
    HasDom,
    ancestor_elements,
    get_classes,
    has_any_class,
    has_class_prefix,
    is_element,
    iter_child_elements,
    iter_child_nodes,
    iter_descendant_elements,
    iter_descendants,
    set_attr,
)
from mf2dom.implied import (
    _has_property_class,
    _is_implied_candidate,
    implied_name,
    implied_photo,
    implied_url,
)
from mf2dom.parser import _first_lang, _split_tokens, parse, parse_async
from mf2dom.properties import (
    _serialize_element,
    _serialize_node,
    parse_dt,
    parse_e,
    parse_p,
    parse_u,
)
from mf2dom.renderer import (
    _embedded_property_prefix,
    _rel_attr,
    _render_e_property,
    _render_item,
    _render_string_property,
    _render_text_property,
    _render_u_object_property,
    _value_vcp_node,
    render,
)
from mf2dom.text import text_content
from mf2dom.urls import parse_srcset, try_urljoin
from mf2dom.vcp import datetime as vcp_datetime
from mf2dom.vcp import normalize_datetime as vcp_normalize_datetime
from mf2dom.vcp import text as vcp_text


def _first_el(html: str, tag: str):
    root = cast("HasDom", JustHTML(html).root)
    return next(el for el in iter_descendant_elements(root) if el.name.lower() == tag)


def test_types_module_import_and_runtime_construction() -> None:
    types = importlib.import_module("mf2dom.types")

    u = types.UrlObject(value="http://example.com/a.jpg", alt="A")
    e = types.EValue(value="hi", html="<b>hi</b>", lang="en")
    rel = types.RelUrl(rels=["tag"], text="t")
    assert u["alt"] == "A"
    assert e["lang"] == "en"
    assert rel["rels"] == ["tag"]

    item = types.Mf2Item(type=["h-card"], properties={})
    doc = types.Mf2Document(items=[item], rels={}, **{"rel-urls": {}})
    assert render(doc).startswith("<main>")


def test_urls_try_urljoin_and_parse_srcset(monkeypatch) -> None:
    assert try_urljoin(None, None) is None
    assert try_urljoin("http://example.com/", "http://x.test/") == "http://x.test/"
    assert try_urljoin(None, "/relative") == "/relative"
    assert try_urljoin("http://example.com/base/", "a") == "http://example.com/base/a"
    assert (
        try_urljoin("http://example.com/base/", "a#frag", allow_fragments=False)
        == "http://example.com/base/a#frag"
    )

    assert parse_srcset("a.jpg 1x, b.jpg 2x, c.jpg", "http://example.com/") == {
        "1x": "http://example.com/a.jpg",
        "2x": "http://example.com/b.jpg",
    }

    monkeypatch.setattr(
        "mf2dom.urls.urljoin",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError("boom")),
    )
    assert try_urljoin("http://example.com/", "a") == "a"


def test_dom_helpers_and_class_splitting() -> None:
    div = _first_el('<div class="a\u00a0b c\t d\n"></div>', "div")
    assert get_classes(div) == ["a\u00a0b", "c", "d"]

    empty = _first_el('<div class=" \t\n\r\f "></div>', "div")
    assert get_classes(empty) == []

    missing = _first_el("<div></div>", "div")
    assert get_classes(missing) == []

    set_attr(missing, "class", "p-name x-y")
    assert has_any_class(missing, {"p-name"}) is True
    assert has_any_class(missing, {"nope"}) is False
    assert has_class_prefix(missing, {"p-", "u-"}) is True
    assert has_class_prefix(missing, {"z-"}) is False

    inner = _first_el('<div id="o"><span id="i"></span></div>', "span")
    ancestors = list(ancestor_elements(inner))
    assert ancestors
    assert ancestors[0].name.lower() == "div"

    root = cast(
        "HasDom",
        JustHTML("<div><template><span></span></template><span></span></div>").root,
    )
    top = next(el for el in iter_descendant_elements(root) if el.name.lower() == "div")
    assert [c.name.lower() for c in iter_child_nodes(top)]  # has children
    assert [c.name.lower() for c in iter_child_elements(top)] == ["span"]

    assert is_element(top) is True
    assert is_element(object()) is False


def test_mf2_name_validation_edge_case() -> None:
    assert is_valid_mf2_name("a1b2") is False


def test_text_content_ignores_doctype_comment_and_drops_tags() -> None:
    root = JustHTML("<!doctype html><!--c--><div>Hi<script>no</script></div>").root
    assert text_content(root).strip() == "Hi"


def test_text_content_img_replacement_paths() -> None:
    div = _first_el('<div>hello<img src="/a.png"></div>', "div")
    assert (
        text_content(div, replace_img=True, base_url="http://example.com")
        == "hello http://example.com/a.png "
    )
    assert (
        text_content(div, replace_img=True, img_to_src=False, base_url="http://example.com")
        == "hello"
    )

    # Non-string text nodes and <img> with no alt/src are ignored.
    @dataclass
    class _Text:
        name: str = "#text"
        data: object = None

    @dataclass
    class _Img:
        name: str = "img"
        attrs: dict[str, str | None] = None  # type: ignore[assignment]
        children: list[object] = None  # type: ignore[assignment]

    assert text_content(_Text()) == ""
    assert text_content(_Img(attrs={}, children=[]), replace_img=True) == ""

    @dataclass
    class _ElementNoChildren:
        name: str = "div"
        attrs: dict[str, str | None] = field(default_factory=dict)

    assert text_content(_ElementNoChildren()) == ""


def test_implied_helpers_and_implied_properties() -> None:
    el = _first_el('<div class="p-name"></div>', "div")
    assert _has_property_class(el) is True
    assert _is_implied_candidate(el) is False

    plain = _first_el("<div></div>", "div")
    assert _is_implied_candidate(plain) is True

    # If the single child is itself a microformat root, it is not a candidate.
    host = _first_el('<div><div class="h-card"></div></div>', "div")
    assert implied_name(host, None) == ""

    img = _first_el('<img alt="  A  B  " src="/p.jpg">', "img")
    assert implied_name(img, None) == "A B"

    photo = _first_el('<img src="/p.jpg" alt="A" srcset="/p1.jpg 1x, /p2.jpg 2x">', "img")
    assert implied_photo(photo, "http://example.com") == {
        "value": "http://example.com/p.jpg",
        "alt": "A",
        "srcset": {
            "1x": "http://example.com/p1.jpg",
            "2x": "http://example.com/p2.jpg",
        },
    }

    obj = _first_el('<object data="/x"></object>', "object")
    assert implied_photo(obj, "http://example.com") == "http://example.com/x"

    srcset_only = _first_el('<img src="/p.jpg" srcset="/p1.jpg 1x">', "img")
    assert implied_photo(srcset_only, "http://example.com") == {
        "value": "http://example.com/p.jpg",
        "srcset": {"1x": "http://example.com/p1.jpg"},
    }

    obj_no_data = _first_el("<object></object>", "object")
    assert implied_photo(obj_no_data, "http://example.com") is None

    host_obj = _first_el("<div><object></object></div>", "div")
    assert implied_photo(host_obj, "http://example.com") is None

    link = _first_el('<a href="/x"></a>', "a")
    assert implied_url(link, "http://example.com") == "http://example.com/x"
    missing_href = _first_el("<a></a>", "a")
    assert implied_url(missing_href, "http://example.com") is None


def test_properties_parse_p_and_u_tag_specific_branches() -> None:
    abbr = _first_el('<abbr title="T"></abbr>', "abbr")
    assert parse_p(abbr, base_url=None) == "T"

    data = _first_el('<data value="V">Ignored</data>', "data")
    assert parse_p(data, base_url=None) == "V"

    img = _first_el('<img alt="A" src="/p.jpg">', "img")
    assert parse_p(img, base_url=None) == "A"

    a = _first_el('<a href="/x"></a>', "a")
    assert parse_u(a, base_url="http://example.com") == "http://example.com/x"

    img_u = _first_el('<img src="/p.jpg" srcset="/p1.jpg 1x">', "img")
    assert parse_u(img_u, base_url="http://example.com") == {
        "value": "http://example.com/p.jpg",
        "srcset": {"1x": "http://example.com/p1.jpg"},
    }

    audio = _first_el('<audio src="/a"></audio>', "audio")
    assert parse_u(audio, base_url="http://example.com") == "http://example.com/a"

    video = _first_el('<video poster="/p"></video>', "video")
    assert parse_u(video, base_url="http://example.com") == "http://example.com/p"

    obj = _first_el('<object data="/d"></object>', "object")
    assert parse_u(obj, base_url="http://example.com") == "http://example.com/d"

    vcp = _first_el('<div><span class="value">/v</span></div>', "div")
    assert parse_u(vcp, base_url="http://example.com") == "http://example.com/v"

    abbr_u = _first_el('<abbr title="/t"></abbr>', "abbr")
    assert parse_u(abbr_u, base_url="http://example.com") == "http://example.com/t"

    data_u = _first_el('<data value="/z"></data>', "data")
    assert parse_u(data_u, base_url="http://example.com") == "http://example.com/z"

    fallback = _first_el("<span>/y</span>", "span")
    assert parse_u(fallback, base_url="http://example.com") == "http://example.com/y"


def test_properties_parse_dt_and_parse_e_serialization() -> None:
    vcp_root = _first_el('<div><time class="value" datetime="2020-01-01 1pm"></time></div>', "div")
    dt = parse_dt(vcp_root, default_date=None)
    assert dt.value == "2020-01-01 13:00"
    assert dt.date == "2020-01-01"

    time_el = _first_el('<time datetime=" 2020-01-02 10:00 "></time>', "time")
    dt2 = parse_dt(time_el, default_date=None)
    assert dt2.value == " 2020-01-02 10:00 "
    assert dt2.date == "2020-01-02"

    time_only = _first_el("<span>10:00</span>", "span")
    dt3 = parse_dt(time_only, default_date="2020-01-03")
    assert dt3.value == "2020-01-03 10:00"
    assert dt3.date == "2020-01-03"

    date_only = _first_el("<span>2020-01-04</span>", "span")
    dt4 = parse_dt(date_only, default_date=None)
    assert dt4.value == "2020-01-04"
    assert dt4.date == "2020-01-04"

    e = _first_el(
        (
            '<div lang="fr">Hello <a href="/hi" download>world</a><!--c-->'
            '<template><a href="/no">no</a></template></div>'
        ),
        "div",
    )
    out = parse_e(e, base_url="http://example.com", root_lang=None, document_lang=None)
    assert out["lang"] == "fr"
    assert out["value"] == "Hello world"
    assert 'href="http://example.com/hi"' in str(out["html"])
    assert "download" in str(out["html"])
    assert "<!--c-->" in str(out["html"])

    # Serialization helpers cover doctype/document/comment/template/unknown branches.
    doc = JustHTML("<!doctype html><!--c--><div><template><a></a></template><img></div>")
    assert "<!--c-->" in _serialize_node(doc.root)
    assert "<template" not in _serialize_node(doc.root)
    assert _serialize_node(123) == ""

    img = _first_el("<img>", "img")
    img.attrs["download"] = None
    assert " download>" in _serialize_element(img)


def test_parser_base_url_lang_rels_and_input_types() -> None:
    html = """
    <!doctype html>
    <html lang="en">
      <head><base href="/base/"></head>
      <body>
        <a rel="tag tag" href="/a" media="screen" hreflang="en" type="text/html" title="T">Link</a>
        <a rel="tag" href="/a">Other</a>
        <link rel="nofollow" href="http://example.com/b">
        <a rel="   " href="/ignored">X</a>
        <a rel="tag">Missing href</a>
      </body>
    </html>
    """
    doc = JustHTML(html)
    parsed = parse(doc, base_url="http://example.com/root")
    assert parsed["rels"]["tag"] == ["http://example.com/a"]
    assert "nofollow" in parsed["rels"]
    assert parsed["rel-urls"]["http://example.com/a"]["media"] == "screen"

    # <base href=""> should be ignored.
    parsed2 = parse('<base href="">', base_url="http://example.com/")
    assert parsed2["rels"] == {}

    assert parse(None)["items"] == []
    assert parse(b"<div></div>")["items"] == []
    assert parse(cast("HasDom", doc.root), base_url="http://example.com")["rels"] == parsed["rels"]

    assert asyncio.run(parse_async("<div></div>"))["items"] == []

    @dataclass
    class _Node:
        name: str
        attrs: dict[str, str | None]
        children: list[object]
        parent: object | None = None

    root = _Node(
        name="root",
        attrs={},
        children=[
            _Node(name="div", attrs={}, children=[]),
            _Node(name="html", attrs={"lang": "xx"}, children=[]),
        ],
    )
    assert _first_lang(root) == "xx"
    assert (
        _first_lang(
            _Node(
                name="root",
                attrs={},
                children=[_Node(name="div", attrs={}, children=[])],
            )
        )
        is None
    )
    assert _split_tokens(None) == []
    assert _split_tokens(" a  b ") == ["a", "b"]

    with pytest.raises(ValueError, match="base_url"):
        parse("<div></div>", base_url="http://a/", url="http://b/")


def test_parser_embedded_e_value_preserves_lang() -> None:
    html = """
    <div class="h-entry">
      <div class="h-card e-content" lang="fr">
        <span class="p-name">Bonjour</span>
      </div>
    </div>
    """
    parsed = parse(html, base_url="http://example.com/")
    content = cast("dict[str, Any]", parsed["items"][0]["properties"]["content"][0])
    assert content["lang"] == "fr"


def test_dom_iter_descendants_handles_non_dom_children() -> None:
    @dataclass
    class _Node:
        name: str
        children: list[object]
        parent: object | None = None

    sentinel = object()
    root = _Node(name="root", children=[sentinel])
    assert list(iter_descendants(root)) == [sentinel]


def test_parser_dt_default_date_inside_embedded_items() -> None:
    html = """
    <div class="h-parent">
      <div class="dt-test h-child">2020-01-01</div>
      <div class="dt-test h-child">10:00</div>
    </div>
    """
    parsed = parse(html)
    test_props = parsed["items"][0]["properties"]["test"]
    item0 = cast("dict[str, Any]", test_props[0])
    item1 = cast("dict[str, Any]", test_props[1])
    assert item0["value"] == "2020-01-01"
    assert item1["value"] == "2020-01-01 10:00"


def test_renderer_unit_helpers_and_rel_rendering() -> None:
    assert _value_vcp_node(None) == ""
    assert 'value="x"' in _value_vcp_node({"value": "x"})
    assert 'value="5"' in _value_vcp_node(5)

    # Test _rel_attr helper
    assert _rel_attr("http://x/", None) == ""
    assert _rel_attr("http://x/", {}) == ""
    assert _rel_attr("http://x/", {"http://other/": {"rels": ["me"]}}) == ""
    assert _rel_attr("http://x/", {"http://x/": {"rels": []}}) == ""
    assert _rel_attr("http://x/", {"http://x/": {"rels": ["me"]}}) == ' rel="me"'
    assert _rel_attr("http://x/", {"http://x/": {"rels": ["me", "authn"]}}) == ' rel="me authn"'

    # Test _render_text_property with rel_urls
    rel_urls: dict[str, Any] = {"http://x/": {"rels": ["me"]}}
    url_with_rel = _render_text_property("url", "http://x/", rel_urls)
    assert 'rel="me"' in url_with_rel
    url_without_rel = _render_text_property("url", "http://y/", rel_urls)
    assert "rel=" not in url_without_rel

    assert _render_string_property("dt", "name", "x").startswith("<time")
    assert _render_string_property("u", "url", "http://x/").startswith("<a")
    assert _render_string_property("e", "content", "x").startswith("<div")
    # p-name uses <strong> for semantic emphasis
    assert _render_string_property("p", "name", "x").startswith("<strong")

    # Test _render_string_property with rel_urls for u prefix
    rel_urls2: dict[str, Any] = {"http://x/": {"rels": ["me"]}}
    u_with_rel = _render_string_property("u", "url", "http://x/", rel_urls2)
    assert 'rel="me"' in u_with_rel
    u_without_rel = _render_string_property("u", "url", "http://y/", rel_urls2)
    assert "rel=" not in u_without_rel

    assert "&lt;b&gt;" in _render_e_property("content", cast("Any", {"value": "<b>", "html": None}))

    img = _render_u_object_property(
        "photo",
        {
            "value": "http://example.com/a.png",
            "srcset": {
                "2x": "http://example.com/a2.png",
                "1x": "http://example.com/a1.png",
            },
        },
    )
    assert 'srcset="http://example.com/a1.png 1x, http://example.com/a2.png 2x"' in img

    assert _embedded_property_prefix({"type": ["h"], "properties": {}, "html": "<b>x</b>"}) == "e"
    assert (
        _embedded_property_prefix(
            cast("Mf2Item", {"type": ["h"], "properties": {}, "value": {"value": "http://x/"}})
        )
        == "u"
    )
    assert _embedded_property_prefix({"type": ["h"], "properties": {}, "value": "x"}) == "p"

    embedded_e = _render_item(
        {"type": ["h-test"], "html": "<b>x</b>", "properties": {"name": ["y"]}},
        extra_classes=["e-test"],
        as_property=True,
        property_prefix="e",
    )
    assert embedded_e == '<div class="e-test h-test"><b>x</b></div>'

    rendered = render(
        {
            "items": [{"type": ["h-card"], "id": "x", "properties": {"name": ["A"]}}],
            "rels": {},
            "rel-urls": {
                "http://example.com/": {"rels": ["me"], "text": "Home"},
                "http://example.com/no-rels": {"rels": [], "text": "No rels"},
            },
        },
    )
    assert 'href="http://example.com/" rel="me"' in rendered
    assert 'href="http://example.com/no-rels"' in rendered

    needs_vcp = _render_item(
        {"type": ["h"], "value": "V", "properties": {"name": ["X"]}},
        extra_classes=["p-x"],
        as_property=True,
        property_prefix="p",
    )
    assert 'class="value"' in needs_vcp

    no_html = _render_item(
        {"type": ["h"], "value": "V", "properties": {"name": ["X"]}},
        extra_classes=["e-x"],
        as_property=True,
        property_prefix="e",
    )
    assert "<b>" not in no_html


def test_semantic_html_rendering() -> None:
    """Test semantic HTML element mappings in renderer."""
    # Test semantic root elements
    entry = render({"items": [{"type": ["h-entry"], "properties": {}}], "rels": {}, "rel-urls": {}})
    assert "<article" in entry

    cite = render({"items": [{"type": ["h-cite"], "properties": {}}], "rels": {}, "rel-urls": {}})
    assert "<blockquote" in cite

    # Test email property renders as mailto: link
    email_doc = render(
        {
            "items": [{"type": ["h-card"], "properties": {"email": ["test@example.com"]}}],
            "rels": {},
            "rel-urls": {},
        }
    )
    assert 'href="mailto:test@example.com"' in email_doc
    assert "u-email" in email_doc

    # Test email with existing mailto: prefix
    email_doc2 = render(
        {
            "items": [{"type": ["h-card"], "properties": {"email": ["mailto:test@example.com"]}}],
            "rels": {},
            "rel-urls": {},
        }
    )
    assert 'href="mailto:test@example.com"' in email_doc2

    # Test tel property renders as tel: link
    tel_doc = render(
        {
            "items": [{"type": ["h-card"], "properties": {"tel": ["+1-555-1234"]}}],
            "rels": {},
            "rel-urls": {},
        }
    )
    assert 'href="tel:+1-555-1234"' in tel_doc
    assert "p-tel" in tel_doc

    # Test tel with existing tel: prefix
    tel_doc2 = render(
        {
            "items": [{"type": ["h-card"], "properties": {"tel": ["tel:+1-555-1234"]}}],
            "rels": {},
            "rel-urls": {},
        }
    )
    assert 'href="tel:+1-555-1234"' in tel_doc2

    # Test datetime property renders as <time>
    dt_doc = render(
        {
            "items": [{"type": ["h-entry"], "properties": {"published": ["2024-01-15"]}}],
            "rels": {},
            "rel-urls": {},
        }
    )
    assert "<time" in dt_doc
    assert 'datetime="2024-01-15"' in dt_doc
    assert "dt-published" in dt_doc


def test_rel_attribute_on_u_url_properties() -> None:
    """Test that rel attributes are added to u-url properties when URL is in rel-urls."""
    # Test that u-url inside h-card gets rel="me" when URL is in rel-urls
    doc = render(
        {
            "items": [
                {
                    "type": ["h-card"],
                    "properties": {
                        "name": ["Test User"],
                        "url": ["https://example.com/", "https://twitter.com/test"],
                        "uid": ["https://example.com/"],
                    },
                }
            ],
            "rels": {"me": ["https://twitter.com/test"]},
            "rel-urls": {
                "https://twitter.com/test": {"rels": ["me"], "text": "Twitter"},
            },
        }
    )
    # The twitter URL should have rel="me" inside the h-card
    assert 'class="u-url" href="https://twitter.com/test" rel="me"' in doc
    # The example.com URL should NOT have rel since it's not in rel-urls
    assert 'class="u-url" href="https://example.com/">' in doc
    # The uid should also not have rel
    assert 'class="u-uid" href="https://example.com/">' in doc


def test_rel_attribute_with_multiple_rels() -> None:
    """Test that multiple rel values are properly rendered."""
    doc = render(
        {
            "items": [
                {
                    "type": ["h-card"],
                    "properties": {
                        "url": ["https://github.com/test"],
                    },
                }
            ],
            "rels": {"me": ["https://github.com/test"], "authn": ["https://github.com/test"]},
            "rel-urls": {
                "https://github.com/test": {"rels": ["me", "authn"], "text": "GitHub"},
            },
        }
    )
    # Both rels should be present
    assert 'rel="me authn"' in doc


def test_rel_attribute_in_nested_h_cards() -> None:
    """Test that rel attributes work in nested microformats."""
    doc = render(
        {
            "items": [
                {
                    "type": ["h-entry"],
                    "properties": {
                        "author": [
                            {
                                "type": ["h-card"],
                                "properties": {
                                    "name": ["Author"],
                                    "url": ["https://author.example.com/"],
                                },
                            }
                        ],
                    },
                }
            ],
            "rels": {"me": ["https://author.example.com/"]},
            "rel-urls": {
                "https://author.example.com/": {"rels": ["me"], "text": "Author"},
            },
        }
    )
    # The nested author URL should have rel="me"
    assert 'href="https://author.example.com/" rel="me"' in doc


def test_vcp_datetime_and_normalization_edges() -> None:
    tz_only = _first_el(
        (
            '<div><span class="value">2020-01-01</span><span class="value">10:00</span>'
            '<span class="value">Z</span></div>'
        ),
        "div",
    )
    tz_got = vcp_datetime(tz_only, default_date=None)
    assert tz_got is not None
    value, date = tz_got
    assert value.endswith("Z")
    assert date == "2020-01-01"

    time_tz = _first_el(
        (
            '<div><span class="value">2020-01-01</span>'
            '<time class="value" datetime="10:00-08:00"></time></div>'
        ),
        "div",
    )
    time_got = vcp_datetime(time_tz, default_date=None)
    assert time_got is not None
    value2, _date2 = time_got
    assert value2.endswith("-0800")

    assert vcp_normalize_datetime("not-a-datetime") == "not-a-datetime"
    assert vcp_normalize_datetime("2020-01-01 10:00") == "2020-01-01 10:00"
    assert vcp_normalize_datetime("2020-01-01 12am") == "2020-01-01 00:00"
    assert vcp_normalize_datetime("2020-01-01 1pm") == "2020-01-01 13:00"


def test_vcp_value_title_and_empty_value_nodes() -> None:
    titleless = _first_el('<div><abbr class="value-title"></abbr></div>', "div")
    assert vcp_text(titleless) is None
    assert vcp_datetime(titleless, default_date=None) is None

    empty_values = _first_el(
        (
            '<div><data class="value" value=""></data><abbr class="value" title=""></abbr>'
            '<time class="value" datetime=""></time><span class="value"></span></div>'
        ),
        "div",
    )
    assert vcp_datetime(empty_values, default_date=None) is None

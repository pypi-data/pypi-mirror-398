from __future__ import annotations

from pathlib import Path

from mf2dom import parse, render


def test_roundtrip_isomorphic_and_stable() -> None:
    html1 = """
    <div class="h-card">
      <a class="u-url p-name" href="https://example.com/">Example</a>
      <img class="u-photo" src="/avatar.png" alt="Example avatar">
      <div class="p-note e-content"><p>Hello <a href="/hi">world</a>.</p></div>
    </div>
    """

    json1 = parse(html1, base_url="https://example.com")
    html2 = render(json1)
    json2 = parse(html2, base_url="https://example.com")
    html3 = render(json2)

    assert json2 == json1
    assert html3 == html2


def test_roundtrip_embedded_microformats_from_official_suite() -> None:
    base = (
        Path(__file__).resolve().parents[2]
        / "microformats-tests"
        / "tests"
        / "microformats-v2-unit"
        / "nested"
    )
    html_paths = [
        base / "nested-microformat-mistyped.html",
        base / "tentative-nested-microformat.html",
    ]

    for html_path in html_paths:
        html1 = html_path.read_text(encoding="utf-8")
        json1 = parse(html1, base_url="http://example.test")
        html2 = render(json1)
        json2 = parse(html2, base_url="http://example.test")
        html3 = render(json2)

        assert json2 == json1
        assert html3 == html2

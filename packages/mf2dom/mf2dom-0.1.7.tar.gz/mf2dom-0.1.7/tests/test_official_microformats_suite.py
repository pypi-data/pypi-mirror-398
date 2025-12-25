from __future__ import annotations

import json
from pathlib import Path

import pytest

from mf2dom import parse


def _collect_tests(root: Path) -> list[tuple[Path, Path, str]]:
    out: list[tuple[Path, Path, str]] = []
    for html_path in sorted(root.rglob("*.html")):
        json_path = html_path.with_suffix(".json")
        if not json_path.exists():
            continue
        base_url = (
            "http://example.test"
            if "microformats-v2-unit" in html_path.parts
            else "http://example.com/"
        )
        out.append((html_path, json_path, base_url))
    return out


SUBMODULE_ROOT = Path(__file__).resolve().parent / "microformats-tests" / "tests"


@pytest.mark.parametrize(
    ("html_path", "json_path", "base_url"),
    _collect_tests(SUBMODULE_ROOT / "microformats-v2")
    + _collect_tests(SUBMODULE_ROOT / "microformats-v2-unit"),
    ids=lambda p: str(p),
)
def test_official_suite_v2(html_path: Path, json_path: Path, base_url: str) -> None:
    html = html_path.read_text(encoding="utf-8")
    expected = json.loads(json_path.read_text(encoding="utf-8"))

    got = parse(html, base_url=base_url)
    assert got == expected

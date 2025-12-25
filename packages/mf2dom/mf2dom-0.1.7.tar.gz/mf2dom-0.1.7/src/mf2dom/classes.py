"""Microformats2 class token validation.

The official test suite (`microformats-v2-unit/names-*`) defines additional
constraints beyond "starts with the right prefix". This module encodes those
rules and provides utilities for extracting valid root and property classes.
"""

from __future__ import annotations

import re

_DIGIT_LETTER_RE = re.compile(r"^\d+[a-z]$")
_DIGIT_LETTERS_DIGITS_RE = re.compile(r"^\d+[a-z]+\d+$")
_LETTERS_DIGITS_OPTLETTERS_RE = re.compile(r"^([a-z]+)(\d+)([a-z]*)$")

_ALLOWED_NAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
_MIN_DIGITS_FOR_TRAILING_LETTERS = 2


def is_valid_mf2_name(name: str) -> bool:
    """Validate the mf2 *name* portion after the prefix.

    Based on the official microformats2 parsing test suite:
    - ASCII lowercase letters, digits, and hyphen only
    - no leading/trailing hyphen, no empty segments / no '--'
    - a purely numeric name is invalid ('p-19')
    - numeric-only segments are allowed only as the first segment ('p-6-test')
    - segments starting with a digit must be either:
        - digits+single-letter ('7t')
        - digits+letters+digits ('8t8', '8to8')
    - segments starting with a letter may contain digits; if digits are followed by letters,
      the digit run must be at least 2 ('t11t' valid, 'car1d' invalid)
    """
    if not name:
        return False
    if name[0] == "-" or name[-1] == "-" or "--" in name:
        return False
    if any(ch not in _ALLOWED_NAME_CHARS for ch in name):
        return False

    parts = name.split("-")
    if len(parts) == 1 and parts[0].isdigit():
        return False

    return all(_is_valid_name_part(part, is_first=(idx == 0)) for idx, part in enumerate(parts))


def _is_valid_name_part(part: str, *, is_first: bool) -> bool:
    if part.isdigit():
        return is_first
    if part[0].isdigit():
        return bool(_DIGIT_LETTER_RE.match(part) or _DIGIT_LETTERS_DIGITS_RE.match(part))
    if part.isalpha():
        return True

    match = _LETTERS_DIGITS_OPTLETTERS_RE.match(part)
    if not match:
        return False

    _letters, digits, trailing = match.groups()
    if trailing == "":
        return True
    return len(digits) >= _MIN_DIGITS_FOR_TRAILING_LETTERS


def is_valid_root_class(token: str) -> bool:
    return token.startswith("h-") and is_valid_mf2_name(token[2:])


def is_valid_property_class(token: str) -> bool:
    if token.startswith(("p-", "u-", "e-")):
        return is_valid_mf2_name(token[2:])
    if token.startswith("dt-"):
        return is_valid_mf2_name(token[3:])
    return False


def root_types(classes: list[str]) -> list[str]:
    return sorted({c for c in classes if is_valid_root_class(c)})


def property_classes(classes: list[str]) -> list[str]:
    return [c for c in classes if is_valid_property_class(c)]


def has_root_class(classes: list[str]) -> bool:
    return any(is_valid_root_class(c) for c in classes)

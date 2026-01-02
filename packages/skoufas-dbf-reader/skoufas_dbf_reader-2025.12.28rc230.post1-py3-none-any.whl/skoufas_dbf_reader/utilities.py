"""Utilities for conversions"""

from __future__ import annotations

import os
import re
from functools import cache
from typing import Any

import yaml


def read_yaml_data(code: str) -> Any:
    """Return the only object from a yaml file in the data directory"""
    with open(os.path.join(os.path.dirname(__file__), "data", f"{code}.yml"), encoding="utf-8") as stream:
        parsed_yaml = yaml.safe_load(stream)
        return parsed_yaml[code]


def none_if_empty_or_stripped(i: str | None) -> str | None:
    """Cleanup"""
    if not i:
        return None
    if not i.strip():
        return None
    return i.strip()


@cache
def all_entries() -> list[dict[int, str]]:
    """All entries converted from a DBF file"""
    data = read_yaml_data("entries")
    for entry in data:
        for i in range(0, 31):
            if i not in entry:
                entry[i] = None
    return data


def romanize(greek_text: str | None) -> str:
    """Return the ISO 843:1997 transcription of the input Greek text.
    Any non-Greek characters will be ignored and printed as they were.

    This function is (c) George Schizas, released under the Apache 2,0 licence
    See https://github.com/gschizas/RomanizePython/blob/master/src/romanize/romanize.py
    """

    if not greek_text:
        return ""
    result = ""
    cursor = 0
    while cursor < len(greek_text):
        letter = greek_text[cursor]
        prev_letter = greek_text[cursor - 1] if cursor > 0 else ""
        next_letter = greek_text[cursor + 1] if cursor < len(greek_text) - 1 else ""
        third_letter = greek_text[cursor + 2] if cursor < len(greek_text) - 2 else ""

        is_upper = letter.upper() == letter
        is_upper_next = next_letter.upper() == next_letter
        letter = letter.lower()
        prev_letter = prev_letter.lower()
        next_letter = next_letter.lower()
        third_letter = third_letter.lower()

        simple_translation_greek = "άβδέζήιίϊΐκλνξόπρσςτυύϋΰφωώ"
        simple_translation_latin = "avdeziiiiiklnxoprsstyyyyfoo"

        digraph_translation_greek = "θχψ"
        digraph_translation_latin = "thchps"

        digraph_ypsilon_greek = "αεη"
        digraph_ypsilon_latin = "aei"
        digraph_ypsilon_beta = "βγδζλμνραάεέηήιίϊΐοόυύϋΰωώ"
        digraph_ypsilon_phi = "θκξπστφχψ"

        if letter in simple_translation_greek:
            new_letter = simple_translation_latin[simple_translation_greek.index(letter)]
        elif letter in digraph_translation_greek:
            diphthong_index = digraph_translation_greek.index(letter)
            new_letter = digraph_translation_latin[diphthong_index * 2 : diphthong_index * 2 + 2]
        elif letter in digraph_ypsilon_greek:
            new_letter = digraph_ypsilon_latin[digraph_ypsilon_greek.index(letter)]
            if next_letter in ["υ", "ύ"]:
                if third_letter in digraph_ypsilon_beta:
                    new_letter += "v"
                    cursor += 1
                elif third_letter in digraph_ypsilon_phi:
                    new_letter += "f"
                    cursor += 1
        elif letter == "γ":
            if next_letter == "γ":
                new_letter = "ng"
                cursor += 1
            elif next_letter == "ξ":
                new_letter = "nx"
                cursor += 1
            elif next_letter in "χ":
                new_letter = "nch"
                cursor += 1
            else:
                new_letter = "g"
        elif letter == "μ":
            if next_letter == "π":
                if prev_letter.strip() == "" or third_letter.strip() == "":
                    new_letter = "b"
                    cursor += 1
                else:
                    new_letter = "mp"
                    cursor += 1
            else:
                new_letter = "m"
        elif letter == "ο":
            new_letter = "o"
            if next_letter in ["υ", "ύ"]:
                new_letter += "u"
                cursor += 1
        else:
            new_letter = letter
        if is_upper:
            new_letter = new_letter[0].upper() + (new_letter[1:].upper() if is_upper_next else new_letter[1:].lower())
        result += new_letter
        cursor += 1
    return result


def check_isbn(isbn: str) -> str | None:
    isbn = isbn.replace("-", "").replace(" ", "").upper()
    match = re.search(r"^(\d{9})(\d|X)$", isbn)
    if not match:
        return f"Invalid isbn format (len {len(isbn)})"

    digits = match.group(1)
    check_digit = 10 if match.group(2) == "X" else int(match.group(2))

    result = sum((i + 1) * int(digit) for i, digit in enumerate(digits))
    if (result % 11) == check_digit:
        return None
    return f"Invalid check code {result % 11} != {check_digit}"


def check_issn(issn: str) -> str | None:
    issn = issn.replace("-", "").replace(" ", "").upper()
    match = re.search(r"^(\d{7})(\d|X)$", issn)
    if not match:
        return f"Invalid issn format (len {len(issn)})"

    digits = match.group(1)
    check_digit = 10 if match.group(2) == "X" else int(match.group(2))
    result = sum((i + 1) * int(digit) for i, digit in enumerate(digits))
    if (result % 11) == check_digit:
        return None
    return f"Invalid check code {result % 11} != {check_digit}"


def check_ean(ean: str) -> str | None:
    ean = ean.replace("-", "").replace(" ", "").upper()
    match = re.search(r"^(\d+)(\d)$", ean)
    if not match:
        return "Invalid ean format"
    if len(ean) not in (14, 13, 12, 8):
        return f"Invalid ean format (len {len(ean)})"

    digits = match.group(1)
    check_digit = match.group(2)
    result = str((10 - sum((3, 1)[i % 2] * int(n) for i, n in enumerate(reversed(digits)))) % 10)
    if result == check_digit:
        return None
    return f"Invalid check code {result} != {check_digit}"


def is_valid_dewey_strict(d: str):
    strict_dewey_res = [
        re.compile(r"[0-9]{3}\.[0-9]+ [^0-9]+"),
        re.compile(r"[0-9]{3}\.[0-9]+"),
        re.compile(r"[0-9]{3} [^0-9]+"),
        re.compile(r"[0-9]{3}"),
    ]
    for dewey_re in strict_dewey_res:
        if dewey_re.fullmatch(d):
            return True
    return False

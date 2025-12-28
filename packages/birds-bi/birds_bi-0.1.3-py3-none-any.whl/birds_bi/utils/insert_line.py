from __future__ import annotations

import re
from collections.abc import Sequence


def find_string_line_number(
    lines: Sequence[str],
    needle: str,
    *,
    ignore_case: bool = True,
) -> int | None:

    flags = re.IGNORECASE if ignore_case else 0
    pattern = re.compile(re.escape(needle), flags)

    for line_number, line in enumerate(lines, start=1):
        if pattern.search(line):
            return line_number

    return None


def var_insert_line(
    text: str,
    new_line: str,
    needle: str,
) -> str:
    lines = text.splitlines(keepends=True)

    line_number = find_string_line_number(lines, needle)
    if line_number is None:
        return text

    lines.insert(line_number, new_line)

    return "".join(lines)

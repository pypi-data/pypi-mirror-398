from __future__ import annotations

import re

from birds_bi.sql.models import SqlBatch


def split_sql_batches(sql: str) -> list[SqlBatch]:
    """Split a SQL script into batches using ``GO`` as separator.

    The splitter is conservative and understands:

    - ``GO`` as a batch separator only when it appears on its own line
    - Single‑line comments (``--``)
    - Block comments (``/* ... */``)
    - String literals with escaped single quotes

    Each batch is returned as a :class:`SqlBatch` with a 1‑based index and its
    content has single quotes doubled, which is convenient for embedding in
    dynamic SQL strings.
    """

    if not sql:
        return []

    go_line = re.compile(r"^\s*GO(?:\s+\d+)?\s*;?\s*$", re.IGNORECASE)

    batches: list[str] = []
    current: list[str] = []

    in_block_comment = False
    in_string = False  # single quotes '...'

    # Work line-by-line to detect GO on its own line
    lines = sql.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for raw_line in lines:
        line = raw_line

        # If we're not inside a string or block comment, and the line is a GO line, split.
        if not in_string and not in_block_comment and go_line.match(line):
            batch_text = "\n".join(current).strip()
            if batch_text:
                batches.append(batch_text)
            current = []
            continue

        # State machine to handle quotes and /* */ across lines
        j = 0
        while j < len(line):
            ch = line[j]
            nxt = line[j + 1] if j + 1 < len(line) else ""

            if in_block_comment:
                if ch == "*" and nxt == "/":
                    in_block_comment = False
                    j += 2
                else:
                    j += 1
                continue

            if in_string:
                if ch == "'":
                    # Handle escaped single quote ('')
                    if nxt == "'":
                        j += 2
                    else:
                        in_string = False
                        j += 1
                else:
                    j += 1
                continue

            # Not in string or block comment here
            if ch == "-" and nxt == "-":
                # Single-line comment: rest of line is comment; stop scanning
                break
            if ch == "/" and nxt == "*":
                in_block_comment = True
                j += 2
                continue
            if ch == "'":
                in_string = True
                j += 1
                continue

            j += 1

        # After processing the line, add it to the current batch
        current.append(raw_line)

    # Append any remaining batch
    tail = "\n".join(current).strip()
    if tail:
        batches.append(tail)

    return [
        SqlBatch(index=i, sql=batch.replace("'", "''"))
        for i, batch in enumerate(batches, start=1)
    ]

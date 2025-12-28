from __future__ import annotations


def bool_to_int(value: object) -> int:
    """Convert any truthy / falsy value to ``1`` or ``0``."""

    return 1 if bool(value) else 0

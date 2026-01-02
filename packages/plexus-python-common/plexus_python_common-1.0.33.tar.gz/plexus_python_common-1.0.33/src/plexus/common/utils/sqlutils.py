__all__ = [
    "escape_sql_like",
]


def escape_sql_like(s: str | None) -> str:
    if s is None:
        raise ValueError("input string cannot be None")
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

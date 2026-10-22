import base64
import hashlib
import json
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

BROWSER_DEFAULT_SIZE = 50
BROWSER_MAX_SIZE = 200

PICKER_DEFAULT_SIZE = 30
PICKER_MAX_SIZE = 100

GRID_DEFAULT_SIZE = 100
GRID_MAX_SIZE = 500


class Page(BaseModel, Generic[T]):
    items: list[T]
    pageSize: int
    hasMore: bool
    nextCursor: Optional[str] = None
    total: Optional[int] = None


def make_fingerprint(
    hdr_id: int | str,
    sort: list[tuple[str, str]],
    filters: Optional[dict[str, Any]] = None,
    q: Optional[str] = None,
    schema_version: Optional[str | int] = None,
) -> str:
    payload = {
        "hdr": str(hdr_id),
        "sort": sort,
        "filters": sorted(filters.items()) if filters else [],
        "q": q or "",
        "sv": str(schema_version or 1),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:8]


def encode_cursor(values: dict[str, Any]) -> str:
    raw = json.dumps(values).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("utf-8")
    if len(encoded) > 1024:
        raise ValueError("Cursor exceeds maximum length of 1KB")
    return encoded


def decode_cursor(cursor: Optional[str]) -> Optional[dict[str, Any]]:
    if not cursor:
        return None
    try:
        if len(cursor) > 1024:
            return None
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict) or data.get("v") != 1:
            return None
        return data
    except Exception:
        return None


def resolve_sort(
    known_columns: set[str],
    sort_param: Optional[str],
    default_order: list[tuple[str, str]],
    row_key: Optional[str],
) -> list[tuple[str, str]]:
    """
    Resolves sort parameter into a list of (column_name, direction) tuples.
    Appends row_key as final tie-breaker if not already present.
    Raises ValueError / InvalidSort if unknown column or too many columns.
    """
    from app.core.errors import InvalidSort

    parsed: list[tuple[str, str]] = []
    if sort_param:
        parts = [p.strip() for p in sort_param.split(",") if p.strip()]
        if len(parts) > 2:
            raise InvalidSort("At most 2 sort columns allowed")
        for part in parts:
            sub = part.split(":")
            col = sub[0].strip()
            direction = sub[1].strip().lower() if len(sub) > 1 else "asc"
            if direction not in ("asc", "desc"):
                direction = "asc"
            if col not in known_columns:
                raise InvalidSort(f"Sort column '{col}' is not allowed")
            parsed.append((col, direction))
    else:
        parsed = list(default_order)

    # Ensure row_key is present as tie-breaker
    if row_key and row_key in known_columns:
        if not any(c.lower() == row_key.lower() for c, _ in parsed):
            parsed.append((row_key, "desc" if default_order and default_order[0][1].lower() == "desc" else "asc"))
    elif row_key and row_key not in known_columns:
        pass

    return parsed


def build_keyset_predicate(
    sort: list[tuple[str, str]],
    last_values: list[Any],
) -> tuple[str, list[Any]]:
    """
    Builds keyset pagination predicate using:
    after(c1) OR (eq(c1) AND after(c2)) OR (eq(c1) AND eq(c2) AND after(c3)) ...
    """
    if not sort or not last_values or len(sort) != len(last_values):
        return "", []

    clauses: list[str] = []
    params: list[Any] = []

    for i in range(len(sort)):
        and_parts: list[str] = []
        for j in range(i):
            col, _ = sort[j]
            val = last_values[j]
            if val is None:
                and_parts.append(f"x.[{col}] IS NULL")
            else:
                and_parts.append(f"x.[{col}] = ?")
                params.append(val)

        col, direction = sort[i]
        val = last_values[i]
        dir_lower = direction.lower()

        if val is None:
            if dir_lower == "desc":
                continue
            else:
                and_parts.append(f"x.[{col}] IS NOT NULL")
        else:
            if dir_lower == "desc":
                and_parts.append(f"(x.[{col}] < ? OR x.[{col}] IS NULL)")
                params.append(val)
            else:
                and_parts.append(f"x.[{col}] > ?")
                params.append(val)

        if and_parts:
            if len(and_parts) == 1:
                clauses.append(and_parts[0])
            else:
                clauses.append(f"({' AND '.join(and_parts)})")

    if not clauses:
        return "", []

    full_predicate = " OR ".join(clauses)
    return f"({full_predicate})", params


def escape_like_string(q: str) -> str:
    r"""Escapes \, %, _, [ for SQL LIKE ESCAPE '\\'."""
    return (
        q.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("[", "\\[")
    )


def finish_page(
    rows: list[dict[str, Any]],
    page_size: int,
    sort: list[tuple[str, str]],
    hdr_id: Any,
    fingerprint: str,
) -> Page[dict[str, Any]]:
    has_more = len(rows) > page_size
    if has_more:
        items = rows[:page_size]
    else:
        items = rows

    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        last_values = [last_item.get(col) for col, _ in sort]
        cursor_data = {
            "v": 1,
            "m": "keyset",
            "last": last_values,
            "fp": fingerprint,
        }
        next_cursor = encode_cursor(cursor_data)

    return Page(
        items=items,
        pageSize=page_size,
        hasMore=has_more,
        nextCursor=next_cursor,
    )

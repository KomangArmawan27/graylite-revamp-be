from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

def normalize_type(col_type: Optional[str]) -> str:
    if not col_type:
        return "text"
    ct = col_type.strip().lower()
    if ct in ("string", "varchar", "nvarchar", "char", "nchar", "text"):
        return "text"
    if ct in ("int", "integer", "bigint", "smallint", "tinyint"):
        return "integer"
    if ct in ("decimal", "numeric", "money", "smallmoney", "float", "real", "number"):
        return "number" if ct in ("float", "real", "number") else "money"
    if ct in ("date",):
        return "date"
    if ct in ("datetime", "datetime2", "smalldatetime", "datetimeoffset"):
        return "datetime"
    if ct in ("bit", "boolean"):
        return "boolean"
    return "text"

def normalize_value(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val) if val % 1 else int(val)
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return val

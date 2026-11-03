import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

def clean_caption(caption: str | None) -> str:
    if not caption:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', caption)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def normalize_type(col_uitype: str | None = None, col_datatype: str | None = None, col_name: str | None = None, scale: int = 0) -> str:
    c_name = (col_name or "").strip().lower()
    if col_uitype:
        ut = col_uitype.strip().lower()
        if ut in ("integer", "number", "money", "date", "datetime", "boolean", "image", "document"):
            return ut
        if ut in ("float", "real"):
            return "number"
        if ut in ("decimal", "numeric"):
            return "money" if scale > 0 or "total" in c_name or "amount" in c_name or "price" in c_name or "vat" in c_name else "number"
    if col_datatype:
        dt = col_datatype.strip().lower()
        if dt in ("number", "float", "real", "decimal", "numeric", "money", "smallmoney"):
            if scale == 0 and c_name.endswith("_id") and c_name != "doc_id":
                return "integer"
            if dt in ("money", "smallmoney") or "total" in c_name or "amount" in c_name or "price" in c_name or "grandtotal" in c_name or "vat" in c_name:
                return "money"
            return "number" if dt in ("float", "real", "number") else "money"
        if dt in ("int", "integer", "bigint", "smallint", "tinyint"):
            return "integer"
        if dt in ("date",):
            return "date"
        if dt in ("datetime", "datetime2", "smalldatetime", "datetimeoffset"):
            return "datetime"
        if dt in ("bit", "boolean"):
            return "boolean"
    if c_name.endswith("_id") or c_name in ("doc_id", "item_id", "class_id", "cust_id"):
        return "integer"
    if "date" in c_name:
        return "date"
    if "total" in c_name or "price" in c_name or "amount" in c_name or "vat" in c_name or "grandtotal" in c_name:
        return "money"
    return "text"

def serialize_row(row: dict, columns: list | None = None) -> dict:
    if not row:
        return {}
    res = {}
    for k, val in row.items():
        if val is None:
            res[k] = None
        elif isinstance(val, Decimal):
            res[k] = format(val, "f")
        elif isinstance(val, datetime):
            res[k] = val.replace(tzinfo=None).isoformat()
        elif isinstance(val, date):
            res[k] = val.isoformat()
        elif isinstance(val, int):
            res[k] = val
        elif isinstance(val, float):
            res[k] = format(Decimal(str(val)), "f")
        else:
            res[k] = val
    return res

def normalize_value(val: Any) -> Any:
    if isinstance(val, Decimal):
        return format(val, "f")
    if isinstance(val, datetime):
        return val.replace(tzinfo=None).isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return val

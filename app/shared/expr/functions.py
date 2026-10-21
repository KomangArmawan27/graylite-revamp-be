from datetime import date, timedelta
from typing import Any, Optional
import math

def TODAY() -> date:
    return date.today()

def DATEADD(n: int, d: Any) -> date:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()
    return d + timedelta(days=int(n))

def FDOM(d: Any) -> date:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()
    return date(d.year, d.month, 1)

def EDOM(d: Any) -> date:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()
    if d.month == 12:
        next_month = date(d.year + 1, 1, 1)
    else:
        next_month = date(d.year, d.month + 1, 1)
    return next_month - timedelta(days=1)

def YEAR(d: Any) -> int:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()
    return d.year

def MONTH(d: Any) -> int:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    elif isinstance(d, datetime):
        d = d.date()
    elif not isinstance(d, date):
        d = date.today()
    return d.month

def ISNA(x: Any, d: Any) -> Any:
    if x is None:
        return d
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return d
    if isinstance(x, str) and not x.strip():
        return d
    return x

MATH_FUNCS = {
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "max": max,
    "min": min,
}

HELPER_FUNCS = {
    "today": TODAY,
    "dateadd": DATEADD,
    "fdom": FDOM,
    "edom": EDOM,
    "year": YEAR,
    "month": MONTH,
    "isna": ISNA,
}

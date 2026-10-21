import base64
import json
from typing import Any, Optional

def encode_cursor(values: dict[str, Any]) -> str:
    raw = json.dumps(values).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")

def decode_cursor(cursor: Optional[str]) -> Optional[dict[str, Any]]:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None

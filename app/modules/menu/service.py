import re
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.modules.meta.service import MetaService
from app.shared.roles import allowed

meta_service = MetaService()

EXCLUDE_PATTERNS = [
    lambda code: "tidak dipakai" in code.lower(),
    lambda code: bool(re.search(r"\.\d{6}$", code)),
    lambda code: any(seg.lower() == "dev" for seg in code.split(".")),
]

def should_exclude(code: str) -> bool:
    trimmed = code.strip()
    return any(pattern(trimmed) for pattern in EXCLUDE_PATTERNS)

def get_menu_items(db: Session, user_roles: List[str]) -> Dict[str, Any]:
    screens = meta_service.list_screens(db, types=["BROWSER"])
    items = []
    
    for s in screens:
        if not s.get("has_expr"):
            continue
        code = (s.get("hdr_code") or "").strip()
        if not code or should_exclude(code):
            continue
        
        hdr_level = s.get("hdr_level")
        if not allowed(hdr_level, user_roles):
            continue

        cap = (s.get("hdr_cap") or "").strip()
        if not cap:
            parts = code.split(".")
            if len(parts) > 1:
                cap = " ".join(parts[1:])
            else:
                cap = code

        segments = code.split(".")
        module = segments[1] if len(segments) >= 2 else (segments[0] if segments else "")
        group = segments[2] if len(segments) >= 4 else None

        items.append({
            "hdrId": s.get("hdr_id"),
            "code": code,
            "caption": cap,
            "type": "browser",
            "module": module,
            "group": group,
            "detailHdrId": s.get("detail_hdr_id"),
        })

    items.sort(key=lambda x: (
        (x["module"] or "").lower(),
        0 if x["group"] is None else 1,
        (x["group"] or "").lower(),
        (x["caption"] or "").lower()
    ))

    return {
        "count": len(items),
        "items": items
    }

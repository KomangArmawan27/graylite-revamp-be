import re
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Dict, List
from app.core.db import get_db_write
from app.core.deps import get_current_user
from app.shared.params import bind
from app.core.errors import AppError
from app.modules.meta.service import MetaService
from app.shared.roles import allowed

router = APIRouter(prefix="/screens", tags=["commands"])
meta_service = MetaService()

@router.post("/{hdrId}/commands/{cmdId}/run")
def run_command(
    hdrId: int,
    cmdId: int,
    payload: dict,
    db: Session = Depends(get_db_write),
    user: dict = Depends(get_current_user),
):
    user_roles = user.get("roles", [])
    screen = meta_service.get_screen(db, hdrId)
    if not allowed(screen.get("hdr_level"), user_roles):
        raise AppError(status_code=403, code="forbidden", message="Access denied")

    sql = "SELECT * FROM [System].[Form.Commands] WHERE cmd_id = :cmdId"
    cmd = db.execute(text(sql), {"cmdId": cmdId}).mappings().first()
    if not cmd or cmd.get("hdr_id") != hdrId:
        raise AppError(status_code=404, code="not_found", message="Command not found")

    if not allowed(cmd.get("cmd_privilege"), user_roles):
        raise AppError(status_code=403, code="forbidden", message="Command permission denied")

    controlexpr = cmd.get("cmd_controlexpr")
    if not controlexpr:
        return {"ok": True, "message": None, "actions": [], "dropped": 0}

    values = payload.get("values", {})
    param_values = {
        "_USERID": user.get("id"),
        "_USERLOGIN": user.get("login"),
        "_CCID": user.get("ccId"),
        **{k: v for k, v in values.items() if not k.startswith("_")}
    }

    statements = [s.strip() for s in controlexpr.split(";") if s.strip()]
    actions = []
    dropped = 0

    for stmt in statements:
        if stmt.lower().startswith("exec") or stmt.lower().startswith("select"):
            try:
                bound_sql, bound_params = bind(stmt, param_values)
                result = db.connection().exec_driver_sql(bound_sql, tuple(bound_params))
                for row in result:
                    for val in row:
                        if isinstance(val, str):
                            v_clean = val.strip()
                            if v_clean == "REFRESHFORM();":
                                actions.append({"type": "refresh"})
                            elif v_clean == "SAVEFORM();":
                                actions.append({"type": "save"})
                            elif v_clean.startswith("alert("):
                                match = re.match(r"alert\('(.*)'\)", v_clean)
                                msg = match.group(1) if match else v_clean
                                actions.append({"type": "alert", "message": msg})
                            else:
                                dropped += 1
            except Exception:
                pass
        else:
            dropped += 1

    db.commit()
    return {
        "ok": True,
        "message": cmd.get("cmd_message"),
        "actions": actions,
        "dropped": dropped,
    }

import re
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from app.core.db import get_db_write
from app.core.deps import get_current_user
from app.shared.params import bind
from app.core.errors import AppError

router = APIRouter(prefix="/commands", tags=["commands"])

@router.post("/{cmdId}/run")
def run_command(
    cmdId: int,
    payload: dict,
    db: Session = Depends(get_db_write),
    user: dict = Depends(get_current_user),
):
    # Fetch command
    sql = "SELECT * FROM [System].[Form.Commands] WHERE cmd_id = :cmdId"
    cmd = db.connection().exec_driver_sql(sql, {"cmdId": cmdId}).mappings().first()
    if not cmd:
        raise AppError(status_code=404, code="not_found", message="Command not found")

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
                # Check if result returns text instructions
                for row in result:
                    for val in row:
                        if isinstance(val, str):
                            # Parse actions
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
            except Exception as e:
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

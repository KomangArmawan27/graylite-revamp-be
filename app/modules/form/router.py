import hashlib
import json
import re
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import InFlight, Replay, idempotency_store
from app.core.config import settings
from app.core.db import get_db, get_db_write
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.modules.meta.service import MetaService
from app.shared.expr.evaluator import evaluate_expression
from app.shared.roles import allowed
from app.shared.types import normalize_value, serialize_row

router = APIRouter(prefix="/forms", tags=["forms"])
meta_service = MetaService()

@router.get("/{hdrId}/new")
def get_new_form(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []), user=user)
    details = meta_service.repo.get_form_details(db, hdrId)
    defaults = {}
    context = {
        "_USERID": user.get("id") if user else 1,
        "_USERLOGIN": user.get("login") if user else "system",
        "_CCID": user.get("ccId") if user else 1,
        "_USERLEVEL": ",".join(user.get("roles", [])),
    }
    for d in details:
        col_name = d.get("col_name")
        default_expr = d.get("col_defaultvalue")
        if col_name and default_expr:
            try:
                val = evaluate_expression(str(default_expr).strip(), context)
                if val is not None:
                    defaults[col_name] = normalize_value(val)
            except Exception:
                pass
    grids_empty = {g_id: {"rows": []} for g_id in meta.get("grids", {}).keys()}
    return {
        "header": defaults,
        "grids": grids_empty,
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.get("/{hdrId}/records/{recordId}")
def get_form_record(hdrId: int, recordId: Any, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []), user=user)
    header = meta_service.get_screen(db, hdrId)
    base_table = header.get("hdr_basetable") or header.get("hdr_expr")
    if not base_table:
        raise AppError(status_code=404, code="not_found", message="Base table not defined")

    if not base_table.lower().startswith("select"):
        query = f"SELECT * FROM {base_table} WHERE [{meta.get('idField', 'id')}] = :id"
    else:
        query = f"SELECT * FROM ({base_table}) x WHERE x.[{meta.get('idField', 'id')}] = :id"

    header_row = db.execute(text(query), {"id": recordId}).mappings().first()
    if not header_row:
        raise AppError(status_code=404, code="not_found", message=f"Record not found: {recordId}")

    grids_data = {}
    for g_id_str, g_meta in meta.get("grids", {}).items():
        try:
            grid_screen = meta_service.get_screen(db, int(g_id_str))
            grid_expr = (grid_screen.get("hdr_expr") or "").strip()
            if grid_expr:
                if not grid_expr.lower().startswith("select"):
                    grid_query = f"SELECT * FROM {grid_expr} WHERE doc_id = :id"
                else:
                    grid_query = f"SELECT * FROM ({grid_expr}) x WHERE x.doc_id = :id"
                g_rows = db.execute(text(grid_query), {"id": recordId}).mappings().all()
                grids_data[g_id_str] = {"rows": [serialize_row(dict(r)) for r in g_rows]}
            else:
                grids_data[g_id_str] = {"rows": []}
        except Exception:
            grids_data[g_id_str] = {"rows": []}

    return {
        "header": serialize_row(dict(header_row)),
        "grids": grids_data,
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.post("/{hdrId}/records")
def create_form_record(
    hdrId: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db_write),
    user: dict = Depends(get_current_user),
):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    
    user_roles = user.get("roles", [])
    if not meta_service.can_add(db, hdrId, user_roles):
        raise AppError(status_code=403, code="forbidden", message="Access denied (role or missing browser)")

    meta = meta_service.get_form_meta(db, hdrId, user_roles, user=user)
    
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed. Please reload.")

    idempotency_key = request.headers.get("Idempotency-Key")
    body_hash = ""
    user_id = user.get("id", 1)
    route_path = request.url.path

    if idempotency_key:
        if not re.match(r"^[A-Za-z0-9_-]{8,64}$", idempotency_key):
            raise AppError(status_code=400, code="bad_request", message="Invalid idempotency key format")
        body_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        
        res = idempotency_store.begin(idempotency_key, user_id, route_path, body_hash)
        if isinstance(res, Replay):
            headers = {**res.headers, "Idempotent-Replay": "true", "X-Request-Id": getattr(request.state, "request_id", "unknown")}
            return Response(content=res.body, status_code=res.status, media_type="application/json", headers=headers)
        elif res == "conflict_body":
            raise AppError(status_code=409, code="key_reused", message="Idempotency key reused with different request body", details=[{"code": "key_reused"}])
        elif isinstance(res, InFlight):
            raise AppError(status_code=409, code="in_progress", message="Request with this idempotency key is already in progress", details=[{"code": "in_progress"}])

    raw_header_data = payload.get("header", {})
    header_data = meta_service.process_header_save(db, hdrId, raw_header_data, user, is_create=True)

    header = meta_service.get_screen(db, hdrId)
    base_table = header.get("hdr_basetable")
    if not base_table:
        raise AppError(status_code=400, code="bad_request", message="Base table not found for form")

    cols = list(header_data.keys())
    if not cols:
        raise AppError(status_code=422, code="validation_failed", message="Empty header payload")

    col_names_sql = ", ".join([f"[{c}]" for c in cols])
    placeholders_sql = ", ".join([f":{c}" for c in cols])
    pk_field = meta.get("idField", "id")

    insert_sql = f"""
    INSERT INTO {base_table} ({col_names_sql})
    OUTPUT INSERTED.[{pk_field}]
    VALUES ({placeholders_sql})
    """
    try:
        row = db.execute(text(insert_sql), header_data).first()
        new_id = row[0] if row else None

        grids_payload = payload.get("grids", {})
        for g_id_str, g_content in grids_payload.items():
            try:
                g_hdr_id = int(g_id_str)
                grid_screen = meta_service.get_screen(db, g_hdr_id)
                grid_base_table = grid_screen.get("hdr_basetable")
                if not grid_base_table:
                    continue

                grid_cols = meta_service.repo.get_grid_columns(db, g_hdr_id)
                parent_field = "doc_id"
                row_number_field = "trans_idx"
                allowed_cols = set()
                for gc in grid_cols:
                    col_name = gc.get("col_name")
                    if col_name:
                        allowed_cols.add(col_name.lower())
                    if gc.get("col_key") == 2:
                        parent_field = col_name
                    elif gc.get("col_key") == 3:
                        row_number_field = col_name

                rows = g_content.get("rows", [])
                for idx, r_data in enumerate(rows, start=1):
                    row_dict = {parent_field: new_id}
                    if row_number_field:
                        row_dict[row_number_field] = r_data.get(row_number_field, idx)

                    for rk, rv in r_data.items():
                        if rk.lower() in allowed_cols and rk.lower() not in (parent_field.lower(), row_number_field.lower() if row_number_field else ""):
                            row_dict[rk] = rv

                    g_cols = list(row_dict.keys())
                    if g_cols:
                        g_col_names = ", ".join([f"[{c}]" for c in g_cols])
                        g_placeholders = ", ".join([f":{c}" for c in g_cols])
                        grid_insert_sql = f"INSERT INTO {grid_base_table} ({g_col_names}) VALUES ({g_placeholders})"
                        db.execute(text(grid_insert_sql), row_dict)
            except Exception as ex:
                raise ValueError(f"Grid {g_id_str} insert error: {ex}")

        db.commit()
        resp_data = get_form_record(hdrId, new_id, db, user)
        if idempotency_key:
            resp_body = json.dumps(resp_data, default=str).encode("utf-8")
            idempotency_store.finish(idempotency_key, user_id, route_path, body_hash, 200, resp_body, {"Content-Type": "application/json"})
        return resp_data
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.put("/{hdrId}/records/{recordId}")
def update_form_record(
    hdrId: int,
    recordId: Any,
    payload: dict,
    db: Session = Depends(get_db_write),
    user: dict = Depends(get_current_user),
):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    
    user_roles = user.get("roles", [])
    meta = meta_service.get_form_meta(db, hdrId, user_roles, user=user)
    header = meta_service.get_screen(db, hdrId)

    if not allowed(header.get("hdr_level"), user_roles):
        raise AppError(status_code=403, code="forbidden", message="Access denied")
    
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed.")

    raw_header_data = payload.get("header", {})
    header_data = meta_service.process_header_save(db, hdrId, raw_header_data, user, is_create=False, record_id=recordId)

    base_table = header.get("hdr_basetable")
    if not base_table:
        raise AppError(status_code=400, code="bad_request", message="Base table not found")
    
    pk_field = meta.get("idField", "id")
    lock_field = settings.EDIT_LOCK_FIELD
    lock_val = settings.EDIT_LOCK_VALUE
    
    try:
        lock_sql = f"SELECT [{lock_field}] FROM {base_table} WITH (UPDLOCK, ROWLOCK) WHERE [{pk_field}] = :id"
        lock_row = db.execute(text(lock_sql), {"id": recordId}).mappings().first()
        if not lock_row:
            raise AppError(status_code=404, code="not_found", message="Record not found")
        
        if lock_field in lock_row and lock_row[lock_field] != lock_val:
            raise AppError(status_code=409, code="conflict", message="Document already in flow (locked)")

        if not header_data:
            return get_form_record(hdrId, recordId, db, user)

        set_clauses = ", ".join([f"[{k}] = :{k}" for k in header_data.keys()])
        update_data = {**header_data, "id": recordId}
        update_sql = f"UPDATE {base_table} SET {set_clauses} WHERE [{pk_field}] = :id"
        
        db.execute(text(update_sql), update_data)
        db.commit()
        return get_form_record(hdrId, recordId, db, user)
    except AppError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.delete("/{hdrId}/records/{recordId}")
def delete_form_record(
    hdrId: int,
    recordId: Any,
    db: Session = Depends(get_db_write),
    user: dict = Depends(get_current_user),
):
    if not settings.ENABLE_WRITES or not settings.ENABLE_DELETE:
        raise AppError(status_code=403, code="forbidden", message="Deletes are disabled")
    
    user_roles = user.get("roles", [])
    if not meta_service.can_remove(db, hdrId, user_roles):
        raise AppError(status_code=403, code="forbidden", message="Access denied")

    meta = meta_service.get_form_meta(db, hdrId, user_roles, user=user)
    header = meta_service.get_screen(db, hdrId)
    base_table = header.get("hdr_basetable")
    if not base_table:
        raise AppError(status_code=400, code="bad_request", message="Base table not found")

    pk_field = meta.get("idField", "id")
    lock_field = settings.EDIT_LOCK_FIELD
    lock_val = settings.EDIT_LOCK_VALUE

    try:
        lock_sql = f"SELECT [{lock_field}] FROM {base_table} WITH (UPDLOCK, ROWLOCK) WHERE [{pk_field}] = :id"
        lock_row = db.execute(text(lock_sql), {"id": recordId}).mappings().first()
        if not lock_row:
            raise AppError(status_code=404, code="not_found", message="Record not found")
        
        if lock_field in lock_row and lock_row[lock_field] != lock_val:
            raise AppError(status_code=409, code="conflict", message="Document already in flow (locked)")

        delete_sql = f"DELETE FROM {base_table} WHERE [{pk_field}] = :id"
        db.execute(text(delete_sql), {"id": recordId})
        db.commit()
        return {"ok": True}
    except AppError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.get("/{hdrId}/fields/{name}/options")
def get_field_options(
    hdrId: int,
    name: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []), user=user)
    sql = """
    SELECT d.col_uitype, d.col_controlexpr 
    FROM [System].[Form.Details] d
    WHERE d.hdr_id = :hdr_id AND d.col_name = :name
    """
    res = db.execute(text(sql), {"hdr_id": hdrId, "name": name}).mappings().first()
    if not res:
        return {"options": []}
    
    uitype = res.get("col_uitype")
    expr = res.get("col_controlexpr")
    
    if uitype == "combobox":
        return {"options": []}
    elif uitype in ("comboquery", "xcomboquery") and expr:
        try:
            rows = db.connection().exec_driver_sql(expr).mappings().all()
            return {"options": [serialize_row(dict(r)) for r in rows]}
        except Exception:
            return {"options": []}
            
    return {"options": []}

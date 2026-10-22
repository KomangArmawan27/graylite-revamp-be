from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Dict
from app.core.db import get_db, get_db_write
from app.core.deps import get_current_user
from app.modules.meta.service import MetaService
from app.core.errors import AppError
from app.core.config import settings

router = APIRouter(prefix="/forms", tags=["forms"])
meta_service = MetaService()

@router.get("/{hdrId}/new")
def get_new_form(hdrId: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []))
    return {
        "header": meta.get("defaults", {}),
        "grids": {},
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.get("/{hdrId}/records/{recordId}")
def get_form_record(hdrId: int, recordId: Any, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []))
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
                grids_data[g_id_str] = {"rows": [dict(r) for r in g_rows]}
            else:
                grids_data[g_id_str] = {"rows": []}
        except Exception:
            grids_data[g_id_str] = {"rows": []}

    return {
        "header": dict(header_row),
        "grids": grids_data,
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.post("/{hdrId}/records")
def create_form_record(hdrId: int, payload: dict, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []))
    
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed. Please reload.")

    header_data = payload.get("header", {})
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
    DECLARE @o TABLE (id BIGINT);
    INSERT INTO {base_table} ({col_names_sql})
    OUTPUT INSERTED.[{pk_field}] INTO @o
    VALUES ({placeholders_sql});
    SELECT id FROM @o;
    """
    try:
        row = db.execute(text(insert_sql), header_data).first()
        new_id = row[0] if row else None
        db.commit()
        return get_form_record(hdrId, new_id, db, user)
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.put("/{hdrId}/records/{recordId}")
def update_form_record(hdrId: int, recordId: Any, payload: dict, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []))
    
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed.")

    header_data = payload.get("header", {})
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
def delete_form_record(hdrId: int, recordId: Any, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_DELETE:
        raise AppError(status_code=501, code="not_implemented", message="Delete is currently disabled")
    return {"ok": True}

@router.get("/{hdrId}/fields/{name}/options")
def get_field_options(
    hdrId: int,
    name: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    meta = meta_service.get_form_meta(db, hdrId, user.get("roles", []))
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
            return {"options": [dict(r) for r in rows]}
        except Exception:
            return {"options": []}
            
    return {"options": []}

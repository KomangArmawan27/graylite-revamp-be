from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Any, Dict
from app.core.db import get_db, get_db_write
from app.core.deps import get_current_user
from app.modules.meta.service import MetaService
from app.core.errors import AppError
from app.core.config import settings

router = APIRouter(prefix="/forms", tags=["forms"])
meta_service = MetaService()

@router.get("/{code}/new")
def get_new_form(code: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, code, user.get("roles", []))
    return {
        "header": meta.get("defaults", {}),
        "grids": {},
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.get("/{code}/{id}")
def get_form_record(code: str, id: Any, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    meta = meta_service.get_form_meta(db, code, user.get("roles", []))
    
    # Get base table from header
    sql = "SELECT hdr_basetable, hdr_expr FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.connection().exec_driver_sql(sql, {"code": code, "id": id}).mappings().first()
    if not res:
        raise AppError(status_code=404, code="not_found", message=f"Form not found: {code}")

    base_table = res.get("hdr_basetable") or res.get("hdr_expr")
    if not base_table:
        raise AppError(status_code=404, code="not_found", message="Base table not defined")

    if not base_table.lower().startswith("select"):
        query = f"SELECT * FROM {base_table} WHERE [{meta.get('idField', 'id')}] = :id"
    else:
        query = f"SELECT * FROM ({base_table}) x WHERE x.[{meta.get('idField', 'id')}] = :id"

    header_row = db.connection().exec_driver_sql(query, {"id": id}).mappings().first()
    if not header_row:
        raise AppError(status_code=404, code="not_found", message=f"Record not found: {id}")

    return {
        "header": dict(header_row),
        "grids": {},
        "schemaVersion": meta.get("schemaVersion"),
    }

@router.post("/{code}")
def create_form_record(code: str, payload: dict, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    meta = meta_service.get_form_meta(db, code, user.get("roles", []))
    
    # Verify schemaVersion
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed. Please reload.")

    header_data = payload.get("header", {})
    
    # Get base table
    sql = "SELECT hdr_basetable FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.connection().exec_driver_sql(sql, {"code": code}).mappings().first()
    if not res or not res.get("hdr_basetable"):
        raise AppError(status_code=400, code="bad_request", message="Base table not found for form")
    
    base_table = res.get("hdr_basetable")

    # Insert header using OUTPUT ... INTO table variable
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
        row = db.connection().exec_driver_sql(insert_sql, header_data).first()
        new_id = row[0] if row else None
        db.commit()
        return get_form_record(code, new_id, db, user)
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.put("/{code}/{id}")
def update_form_record(code: str, id: Any, payload: dict, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_WRITES:
        raise AppError(status_code=403, code="forbidden", message="Writes are disabled")
    meta = meta_service.get_form_meta(db, code, user.get("roles", []))
    
    if payload.get("schemaVersion") != meta.get("schemaVersion"):
        raise AppError(status_code=409, code="schema_stale", message="Form configuration has changed.")

    header_data = payload.get("header", {})
    sql = "SELECT hdr_basetable FROM [System].[Form.Headers] WHERE hdr_code = :code"
    res = db.connection().exec_driver_sql(sql, {"code": code}).mappings().first()
    if not res or not res.get("hdr_basetable"):
        raise AppError(status_code=400, code="bad_request", message="Base table not found")
    
    base_table = res.get("hdr_basetable")
    pk_field = meta.get("idField", "id")

    # Edit lock check if applicable
    lock_field = settings.EDIT_LOCK_FIELD
    lock_val = settings.EDIT_LOCK_VALUE
    
    try:
        # Row lock and edit lock check
        lock_sql = f"SELECT [{lock_field}] FROM {base_table} WITH (UPDLOCK, ROWLOCK) WHERE [{pk_field}] = :id"
        lock_row = db.connection().exec_driver_sql(lock_sql, {"id": id}).mappings().first()
        if not lock_row:
            raise AppError(status_code=404, code="not_found", message="Record not found")
        
        if lock_field in lock_row and lock_row[lock_field] != lock_val:
            raise AppError(status_code=409, code="conflict", message="Document already in flow (locked)")

        set_clauses = ", ".join([f"[{k}] = :{k}" for k in header_data.keys()])
        update_data = {**header_data, "id": id}
        update_sql = f"UPDATE {base_table} SET {set_clauses} WHERE [{pk_field}] = :id"
        
        db.connection().exec_driver_sql(update_sql, update_data)
        db.commit()
        return get_form_record(code, id, db, user)
    except AppError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise AppError(status_code=409, code="conflict", message=str(e))

@router.delete("/{code}/{id}")
def delete_form_record(code: str, id: Any, db: Session = Depends(get_db_write), user: dict = Depends(get_current_user)):
    if not settings.ENABLE_DELETE:
        raise AppError(status_code=501, code="not_implemented", message="Delete is currently disabled")
    return {"ok": True}

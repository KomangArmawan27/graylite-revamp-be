from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.shared.types import normalize_type

class MetaRepository:
    def get_header_by_code(self, db: Session, code: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Headers] WHERE hdr_code = :code"
        res = db.execute(text(sql), {"code": code}).mappings().first()
        return dict(res) if res else None

    def get_screen_by_id(self, db: Session, hdr_id: int) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT h.hdr_id, LTRIM(RTRIM(h.hdr_code)) AS hdr_code, LTRIM(RTRIM(h.hdr_cap)) AS hdr_cap,
               h.hdr_type, h.hdr_level, h.dtl_code, h.hdr_basetable, h.hdr_expr
        FROM [System].[Form.Headers] h
        WHERE h.hdr_id = :hdr_id
        """
        res = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().first()
        return dict(res) if res else None

    def list_screens(self, db: Session) -> List[Dict[str, Any]]:
        sql = """
        SELECT h.hdr_id, LTRIM(RTRIM(h.hdr_code)) AS hdr_code, LTRIM(RTRIM(h.hdr_cap)) AS hdr_cap,
               h.hdr_type, h.hdr_level,
               CASE WHEN LEN(LTRIM(RTRIM(ISNULL(h.hdr_expr, '')))) > 0 THEN 1 ELSE 0 END AS has_expr,
               d.hdr_id AS detail_hdr_id,
               h.dtl_code
        FROM [System].[Form.Headers] h
        LEFT JOIN [System].[Form.Headers] d
               ON LTRIM(RTRIM(d.hdr_code)) = LTRIM(RTRIM(h.dtl_code))
        """
        rows = db.execute(text(sql)).mappings().all()
        return [dict(r) for r in rows]

    def get_browser_columns(self, db: Session, hdr_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Browsers] WHERE hdr_id = :hdr_id ORDER BY col_order"
        rows = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().all()
        return [dict(r) for r in rows]

    def get_form_details(self, db: Session, hdr_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Details] WHERE hdr_id = :hdr_id ORDER BY col_order"
        rows = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().all()
        return [dict(r) for r in rows]

    def get_grid_columns(self, db: Session, hdr_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Grids] WHERE hdr_id = :hdr_id ORDER BY col_order"
        rows = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().all()
        return [dict(r) for r in rows]

    def get_variables(self, db: Session, hdr_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Variables] WHERE hdr_id = :hdr_id ORDER BY var_order"
        rows = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().all()
        return [dict(r) for r in rows]

    def get_commands(self, db: Session, hdr_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[Form.Commands] WHERE hdr_id = :hdr_id ORDER BY cmd_order"
        rows = db.execute(text(sql), {"hdr_id": hdr_id}).mappings().all()
        return [dict(r) for r in rows]

    def infer_columns_from_query(self, db: Session, expr: str) -> List[Dict[str, Any]]:
        # Fallback when no browser/picker columns config exist: SELECT TOP 0 * FROM (<expr>) x
        sql = f"SELECT TOP 0 * FROM ({expr}) x"
        try:
            cursor = db.connection().exec_driver_sql(sql)
            keys = cursor.keys()
            cols = []
            for idx, k in enumerate(keys):
                cols.append({
                    "col_id": idx + 1,
                    "col_order": idx + 1,
                    "col_name": k,
                    "col_cap": k.replace("_", " ").title(),
                    "col_type": "text",
                    "col_scale": 0,
                    "col_width": 100,
                    "col_hide": False,
                    "col_key": 1 if idx == 0 else 0,
                    "col_readonly": True,
                })
            return cols
        except Exception:
            return []

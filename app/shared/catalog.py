import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings

_catalog_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}

def get_table_catalog(db: Session, table_name: str) -> List[Dict[str, Any]]:
    now = time.time()
    if table_name in _catalog_cache:
        cached_time, columns = _catalog_cache[table_name]
        if now - cached_time < settings.CONFIG_CACHE_TTL_SEC:
            return columns

    sql = """
    SELECT c.name,
           t.name AS type_name,
           c.max_length, c.precision, c.scale,
           c.is_nullable, c.is_identity, c.is_computed,
           OBJECT_DEFINITION(c.default_object_id) AS default_definition
    FROM sys.columns c
    JOIN sys.types t ON t.user_type_id = c.user_type_id
    WHERE c.object_id = OBJECT_ID(:table_name);
    """
    try:
        result = db.connection().exec_driver_sql(sql, {"table_name": table_name})
        columns = []
        for row in result:
            columns.append({
                "name": row[0],
                "type_name": row[1],
                "max_length": row[2],
                "precision": row[3],
                "scale": row[4],
                "is_nullable": bool(row[5]),
                "is_identity": bool(row[6]),
                "is_computed": bool(row[7]),
                "default_definition": row[8],
            })
        _catalog_cache[table_name] = (now, columns)
        return columns
    except Exception as e:
        # Return empty list if table not found or error
        return []

def clear_catalog_cache():
    _catalog_cache.clear()

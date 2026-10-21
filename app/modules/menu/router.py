from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.shared.roles import allowed

router = APIRouter(tags=["menu"])

@router.get("/menu")
def get_menu(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_roles = user.get("roles", [])
    try:
        # Query tree/menu table if exists, e.g. [System].[Tree.Menu] or similar
        sql = "SELECT * FROM [System].[Tree.Menu]"
        rows = db.connection().exec_driver_sql(sql).mappings().all()
        items = []
        for r in rows:
            target = r.get("object_command") or r.get("object_code")
            # If target screen visible to user
            items.append({
                "id": r.get("object_id"),
                "parentId": r.get("object_parent"),
                "name": r.get("object_name"),
                "target": target,
            })
        return items
    except Exception:
        # Fallback empty menu if table doesn't exist yet
        return []

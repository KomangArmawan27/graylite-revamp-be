from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.menu.service import get_menu_items
from app.modules.menu.schemas import MenuResponse

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("", response_model=MenuResponse)
def get_menu(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_roles = user.get("roles", [])
    return get_menu_items(db, user_roles)

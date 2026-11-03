from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthRepository:
    def get_user_by_login(self, db: Session, login: str) -> dict[str, Any] | None:
        sql = "SELECT * FROM [System].[User.Management] WHERE LOWER(user_login) = LOWER(:login)"
        res = db.execute(text(sql), {"login": login}).mappings().first()
        return dict(res) if res else None

    def update_last_login(self, db: Session, user_id: int):
        sql = "UPDATE [System].[User.Management] SET user_lastlogin = GETDATE() WHERE user_id = :user_id"
        db.execute(text(sql), {"user_id": user_id})
        db.commit()

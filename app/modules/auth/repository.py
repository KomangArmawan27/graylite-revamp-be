from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

class AuthRepository:
    def get_user_by_login(self, db: Session, login: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM [System].[User.Management] WHERE LOWER(user_login) = LOWER(:login)"
        res = db.connection().exec_driver_sql(sql, {"login": login}).mappings().first()
        return dict(res) if res else None

    def update_last_login(self, db: Session, user_id: int):
        sql = "UPDATE [System].[User.Management] SET user_lastlogin = GETDATE() WHERE user_id = :user_id"
        db.connection().exec_driver_sql(sql, {"user_id": user_id})
        db.commit()

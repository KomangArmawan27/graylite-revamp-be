from typing import Optional, List

def allowed(role_list: Optional[str], user_roles: List[str]) -> bool:
    """Exact-name match. 'All' allows everyone. Empty or None means denied."""
    if not role_list or not role_list.strip():
        return False
    wanted = {t.strip().casefold() for t in role_list.split(",") if t.strip()}
    if "all" in wanted:
        return True
    have = {r.strip().casefold() for r in user_roles}
    return bool(wanted & have)

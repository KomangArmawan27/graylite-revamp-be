import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.modules.meta.repository import MetaRepository
from app.shared.types import normalize_type
from app.shared.roles import allowed
from app.core.config import settings

repo = MetaRepository()

_screen_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
_single_screen_cache: Dict[int, tuple[float, Dict[str, Any]]] = {}

def clear_meta_cache():
    _screen_cache.clear()
    _single_screen_cache.clear()

def _compute_schema_version(header: dict, children: list) -> str:
    canonical = {
        "header": {k: v for k, v in header.items() if k != "created_date"},
        "children": sorted([{k: v for k, v in c.items() if k != "created_date"} for c in children], key=lambda x: (x.get("col_order", x.get("var_order", x.get("cmd_order", 0))), x.get("col_id", x.get("var_id", x.get("cmd_id", 0)))))
    }
    raw = json.dumps(canonical, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:8]

def compute_browser_layout(columns: List[Dict[str, Any]]) -> Dict[str, Any]:
    visible = [c for c in columns if not c.get("col_hide", False)]
    
    # title
    title = None
    for c in visible:
        name = c.get("col_name", "").lower()
        if "no" in name or "code" in name or name == "doc_no":
            title = c.get("col_name")
            break
    if not title and visible:
        for c in visible:
            if c.get("col_type") == "text":
                title = c.get("col_name")
                break
    if not title and visible:
        title = visible[0].get("col_name")

    # date
    date_col = None
    for c in visible:
        if c.get("col_key") == 4:
            date_col = c.get("col_name")
            break
    if not date_col:
        for c in visible:
            if c.get("col_type") in ("date", "datetime"):
                date_col = c.get("col_name")
                break

    # subtitle
    subtitle = None
    for c in visible:
        name = c.get("col_name")
        if name != title and name != date_col and c.get("col_type") == "text":
            subtitle = name
            break

    # badge
    badges = []
    for c in visible:
        name = c.get("col_name", "").lower()
        if "state" in name or "status" in name or "flow" in name or c.get("col_type") == "boolean":
            if c.get("col_name") not in (title, subtitle, date_col):
                badges.append(c.get("col_name"))
        if len(badges) >= 2:
            break

    # metrics
    metrics = []
    for c in visible:
        ct = c.get("col_type")
        name = c.get("col_name", "").lower()
        if ct in ("money", "number", "integer") and "id" not in name:
            if c.get("col_name") not in (title, subtitle, date_col):
                metrics.append(c.get("col_name"))
        if len(metrics) >= 3:
            break

    used = {title, date_col, subtitle} | set(badges) | set(metrics)
    details = [c.get("col_name") for c in visible if c.get("col_name") not in used and c.get("col_name")]

    return {
        "title": title or "",
        "date": date_col or "",
        "subtitle": subtitle or "",
        "badge": badges,
        "metrics": metrics,
        "details": details,
    }

class MetaService:
    def get_screen(self, db: Session, hdr_id: int) -> Dict[str, Any]:
        now = time.time()
        if hdr_id in _single_screen_cache:
            cached_time, screen = _single_screen_cache[hdr_id]
            if now - cached_time < settings.CONFIG_CACHE_TTL_SEC:
                return screen

        screen = repo.get_screen_by_id(db, hdr_id)
        if not screen:
            from app.core.errors import AppError
            raise AppError(status_code=404, code="not_found", message=f"Screen not found: {hdr_id}")

        _single_screen_cache[hdr_id] = (now, screen)
        return screen

    def list_screens(self, db: Session, types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        now = time.time()
        cache_key = "all"
        if cache_key in _screen_cache:
            cached_time, screens = _screen_cache[cache_key]
            if now - cached_time < settings.CONFIG_CACHE_TTL_SEC:
                res = screens
            else:
                res = repo.list_screens(db)
                _screen_cache[cache_key] = (now, res)
        else:
            res = repo.list_screens(db)
            _screen_cache[cache_key] = (now, res)

        if types:
            types_upper = {t.upper() for t in types}
            res = [s for s in res if (s.get("hdr_type") or "").upper() in types_upper]
        return res

    def resolve_hdr_id(self, db: Session, code: Optional[str]) -> Optional[int]:
        if not code:
            return None
        screens = self.list_screens(db)
        c_lower = code.strip().lower()
        for s in screens:
            if (s.get("hdr_code") or "").strip().lower() == c_lower:
                return s.get("hdr_id")
        return None

    def get_browser_meta(self, db: Session, hdr_id: int, user_roles: List[str]) -> Dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "BROWSER":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected BROWSER, got {header.get('hdr_type')}")

        columns = repo.get_browser_columns(db, hdr_id)
        if not columns and header.get("hdr_expr"):
            columns = repo.infer_columns_from_query(db, header.get("hdr_expr"))

        variables = repo.get_variables(db, hdr_id)
        commands = repo.get_commands(db, hdr_id)

        all_children = columns + variables + commands
        schema_version = _compute_schema_version(header, all_children)

        row_key = "id"
        date_col = "date"
        for c in columns:
            if c.get("col_key") == 1:
                row_key = c.get("col_name")
            if c.get("col_key") == 4:
                date_col = c.get("col_name")

        formatted_columns = []
        for c in columns:
            formatted_columns.append({
                "name": c.get("col_name"),
                "caption": c.get("col_cap") or c.get("col_name", "").replace("_", " ").title(),
                "type": normalize_type(c.get("col_type")),
                "hidden": bool(c.get("col_hide")),
                "scale": int(c.get("col_scale") or 0),
                "width": int(c.get("col_width") or 100),
            })

        filters = []
        for v in variables:
            if v.get("var_uitype"):
                filters.append({
                    "name": v.get("var_name"),
                    "label": v.get("var_remark") or v.get("var_name"),
                    "type": normalize_type(v.get("var_datatype") or "text"),
                    "default": v.get("var_aggr"),
                    "required": not bool(v.get("var_nullable", True)),
                    "hidden": bool(v.get("var_hide")),
                })

        can_add = allowed(header.get("doc_header"), user_roles) and bool(header.get("dtl_code"))
        can_remove = False

        layout = compute_browser_layout(columns)

        allowed_commands = []
        for cmd in commands:
            if allowed(cmd.get("cmd_privilege"), user_roles):
                allowed_commands.append({
                    "id": cmd.get("cmd_id"),
                    "name": cmd.get("cmd_name"),
                    "confirm": cmd.get("cmd_message") if cmd.get("cmd_type") == "OKCANCEL" else None,
                    "order": cmd.get("cmd_order"),
                })

        dtl_code = header.get("dtl_code")
        detail_hdr_id = self.resolve_hdr_id(db, dtl_code) if dtl_code else None

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": header.get("hdr_cap") or "",
            "schemaVersion": schema_version,
            "rowKey": row_key,
            "dateColumn": date_col,
            "detailCode": dtl_code,
            "detailHdrId": detail_hdr_id,
            "canAdd": can_add,
            "canRemove": can_remove,
            "style": header.get("param1") or "Fit",
            "columns": formatted_columns,
            "filters": filters,
            "layout": layout,
            "commands": allowed_commands,
        }

    def get_grid_meta(self, db: Session, hdr_id: int, user_roles: List[str]) -> Dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "GRID":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected GRID, got {header.get('hdr_type')}")

        columns = repo.get_grid_columns(db, hdr_id)
        if not columns and header.get("hdr_expr"):
            columns = repo.infer_columns_from_query(db, header.get("hdr_expr"))

        row_key = "id"
        for c in columns:
            if c.get("col_key") == 1:
                row_key = c.get("col_name")

        formatted_columns = []
        for c in columns:
            picker_code = c.get("col_controlexpr") if c.get("col_uitype") == "picker" else None
            picker_hdr_id = self.resolve_hdr_id(db, picker_code) if picker_code else None
            col_meta = {
                "name": c.get("col_name"),
                "caption": c.get("col_cap") or c.get("col_name", "").replace("_", " ").title(),
                "type": normalize_type(c.get("col_type")),
                "hidden": bool(c.get("col_hide")),
                "scale": int(c.get("col_scale") or 0),
                "width": int(c.get("col_width") or 100),
            }
            if picker_code:
                col_meta["pickerCode"] = picker_code
                col_meta["pickerHdrId"] = picker_hdr_id
            formatted_columns.append(col_meta)

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": header.get("hdr_cap") or "",
            "rowKey": row_key,
            "columns": formatted_columns,
        }

    def get_picker_meta(self, db: Session, hdr_id: int, user_roles: List[str]) -> Dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "PICKER":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected PICKER, got {header.get('hdr_type')}")

        columns = repo.get_browser_columns(db, hdr_id)
        if not columns and header.get("hdr_expr"):
            columns = repo.infer_columns_from_query(db, header.get("hdr_expr"))

        formatted_columns = []
        for c in columns:
            formatted_columns.append({
                "name": c.get("col_name"),
                "caption": c.get("col_cap") or c.get("col_name", "").replace("_", " ").title(),
                "type": normalize_type(c.get("col_type")),
                "hidden": bool(c.get("col_hide")),
            })

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": header.get("hdr_cap") or "",
            "columns": formatted_columns,
        }

    def get_form_meta(self, db: Session, hdr_id: int, user_roles: List[str]) -> Dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "DETAIL":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected DETAIL, got {header.get('hdr_type')}")

        details = repo.get_form_details(db, hdr_id)
        variables = repo.get_variables(db, hdr_id)
        commands = repo.get_commands(db, hdr_id)

        all_children = details + variables + commands
        schema_version = _compute_schema_version(header, all_children)

        id_field = "id"
        title_fields = []
        for d in details:
            if d.get("col_PK") == 1:
                id_field = d.get("col_name")
            if d.get("col_PK") in (4, 5):
                if d.get("col_name"):
                    title_fields.append(d.get("col_name"))

        tabs_map: Dict[str, List[Any]] = {}
        grids_map: Dict[str, Any] = {}

        for d in details:
            tab = d.get("tab_name") or "General"
            if tab not in tabs_map:
                tabs_map[tab] = []
            
            uitype = (d.get("col_uitype") or "text").strip().lower()
            field_meta = {
                "name": d.get("col_name") or "",
                "caption": d.get("col_caption") or "",
                "widget": uitype,
                "dataType": normalize_type(d.get("col_datatype")),
                "readonly": bool(d.get("col_readonly")),
                "hidden": bool(d.get("col_hide")),
                "update": bool(d.get("col_update")),
                "inlineWithPrevious": d.get("col_offset") == -1,
            }
            if uitype == "picker":
                picker_code = d.get("col_controlexpr")
                picker_hdr_id = self.resolve_hdr_id(db, picker_code)
                field_meta["pickerCode"] = picker_code
                field_meta["pickerHdrId"] = picker_hdr_id
            elif uitype in ("grid",):
                grid_code = d.get("col_controlexpr")
                grid_hdr_id = self.resolve_hdr_id(db, grid_code)
                field_meta["gridCode"] = grid_code
                field_meta["gridHdrId"] = grid_hdr_id
                field_meta["saveWithForm"] = bool(d.get("col_update"))
                if grid_hdr_id:
                    try:
                        grids_map[str(grid_hdr_id)] = self.get_grid_meta(db, grid_hdr_id, user_roles)
                    except Exception:
                        pass
            elif uitype == "formula":
                field_meta["expression"] = d.get("col_controlexpr")
            elif uitype == "combobox":
                field_meta["options"] = []

            tabs_map[tab].append(field_meta)

        tabs = [{"name": t_name, "fields": t_fields} for t_name, t_fields in tabs_map.items()]

        can_save = allowed(header.get("hdr_level"), user_roles)

        allowed_commands = []
        for cmd in commands:
            if allowed(cmd.get("cmd_privilege"), user_roles):
                allowed_commands.append({
                    "id": cmd.get("cmd_id"),
                    "name": cmd.get("cmd_name"),
                    "confirm": cmd.get("cmd_message"),
                    "order": cmd.get("cmd_order"),
                })

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": header.get("hdr_cap") or "",
            "schemaVersion": schema_version,
            "idField": id_field,
            "titleFields": title_fields,
            "docHeader": header.get("doc_header", "").strip() or None,
            "canSave": can_save,
            "journalView": bool(header.get("dtl_journal")),
            "tabs": tabs,
            "variables": [{"name": v.get("var_name"), "from": v.get("var_controlexpr")} for v in variables],
            "grids": grids_map,
            "defaults": {},
            "commands": allowed_commands,
        }

import hashlib
import json
import time
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.modules.meta.repository import MetaRepository
from app.shared.types import normalize_type, clean_caption, serialize_row
from app.shared.roles import allowed
from app.shared.expr.evaluator import evaluate_expression
from app.core.config import settings

logger = logging.getLogger("erp-api")
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

    subtitle = None
    for c in visible:
        name = c.get("col_name")
        if name != title and name != date_col and c.get("col_type") == "text":
            subtitle = name
            break

    badges = []
    for c in visible:
        name = c.get("col_name", "").lower()
        if ("state" in name or "status" in name or "flow" in name or c.get("col_type") == "boolean") and c.get("col_name") not in (title, subtitle, date_col):
            badges.append(c.get("col_name"))
        if len(badges) >= 2:
            break

    metrics = []
    for c in visible:
        ct = c.get("col_type")
        name = c.get("col_name", "").lower()
        if ct in ("money", "number", "integer") and "id" not in name and c.get("col_name") not in (title, subtitle, date_col):
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
    def __init__(self):
        self.repo = repo

    def get_screen(self, db: Session, hdr_id: int) -> dict[str, Any]:
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

    def list_screens(self, db: Session, types: list[str] | None = None) -> list[dict[str, Any]]:
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

    def can_add(self, db: Session, hdr_id: int, user_roles: list[str]) -> bool:
        header = self.get_screen(db, hdr_id)
        hdr_type = (header.get("hdr_type") or "").upper()
        form_code = (header.get("hdr_code") or "").strip().lower()
        if not form_code:
            return False

        if hdr_type == "BROWSER":
            return allowed(header.get("doc_header"), user_roles) and bool(header.get("dtl_code"))

        if hdr_type == "DETAIL":
            browsers = self.list_screens(db, types=["BROWSER"])
            pointing_browsers = [
                b for b in browsers
                if (b.get("dtl_code") or "").strip().lower() == form_code
            ]

            if not pointing_browsers:
                logger.warning(f"No browser points to form hdrId={hdr_id} (code={form_code}). Denying create/delete (fail closed).")
                return False

            for b in pointing_browsers:
                if allowed(b.get("doc_header"), user_roles):
                    return True

            return False

        return False

    def can_remove(self, db: Session, hdr_id: int, user_roles: list[str]) -> bool:
        return self.can_add(db, hdr_id, user_roles)

    def get_browser_meta(self, db: Session, hdr_id: int, user_roles: list[str]) -> dict[str, Any]:
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
            c_name = c.get("col_name")
            scale = int(c.get("col_scale") or 0)
            formatted_columns.append({
                "name": c_name,
                "caption": clean_caption(c.get("col_cap") or (c_name or "").replace("_", " ").title()),
                "widget": normalize_type(c.get("col_uitype")),
                "type": normalize_type(c.get("col_uitype"), c.get("col_datatype"), c_name, scale),
                "hidden": bool(c.get("col_hide") or False),
                "scale": scale,
                "width": int(c.get("col_width") or 100),
            })

        context = {
            "_USERID": 1,
            "_USERLOGIN": "system",
            "_CCID": 1,
            "_USERLEVEL": ",".join(user_roles),
        }

        filters = []
        for v in variables:
            if v.get("var_uitype"):
                v_name = v.get("var_name")
                raw_default = v.get("var_aggr") or v.get("var_controlexpr")
                evaluated_default = None
                default_expr = None
                if raw_default:
                    try:
                        val = evaluate_expression(str(raw_default).strip(), context)
                        if isinstance(val, (date, datetime)):
                            evaluated_default = val.isoformat()[:10] if normalize_type(v.get("var_uitype"), v.get("var_datatype")) == "date" else val.isoformat()
                        else:
                            evaluated_default = val
                    except Exception:
                        default_expr = str(raw_default)
                        logger.warning(f"Failed to evaluate filter default '{raw_default}' for browser hdrId={hdr_id}")

                f_meta = {
                    "name": v_name,
                    "label": clean_caption(v.get("var_remark") or v_name),
                    "type": normalize_type(v.get("var_uitype"), v.get("var_datatype")),
                    "default": evaluated_default,
                    "required": not bool(v.get("var_nullable", True)),
                    "hidden": bool(v.get("var_hide") or False),
                }
                if default_expr:
                    f_meta["defaultExpression"] = default_expr
                filters.append(f_meta)

        can_add = allowed(header.get("doc_header"), user_roles) and bool(header.get("dtl_code"))
        can_remove = can_add

        layout = compute_browser_layout(columns)

        allowed_commands = []
        for cmd in commands:
            if allowed(cmd.get("cmd_privilege"), user_roles):
                allowed_commands.append({
                    "id": cmd.get("cmd_id"),
                    "name": clean_caption(cmd.get("cmd_name")),
                    "confirm": clean_caption(cmd.get("cmd_message")) if cmd.get("cmd_type") == "OKCANCEL" else None,
                    "order": cmd.get("cmd_order"),
                })

        dtl_code = header.get("dtl_code")
        detail_hdr_id = self.resolve_hdr_id(db, dtl_code) if dtl_code else None

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": clean_caption(header.get("hdr_cap")),
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

    def build_grid_meta(self, db: Session, hdr_id: int, user_roles: list[str], form_grid_field: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "GRID":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected GRID, got {header.get('hdr_type')}")

        columns = repo.get_grid_columns(db, hdr_id)
        if not columns and header.get("hdr_expr"):
            columns = repo.infer_columns_from_query(db, header.get("hdr_expr"))

        variables = repo.get_variables(db, hdr_id)

        row_key = "id"
        parent_field = None
        row_number_field = None
        for c in columns:
            col_key = c.get("col_key")
            c_name = c.get("col_name")
            if col_key == 1:
                row_key = c_name
            elif col_key == 2:
                parent_field = c_name
            elif col_key == 3:
                row_number_field = c_name

        can_add_remove = bool(header.get("hdr_addremove", 1))
        save_with_form = bool(form_grid_field.get("col_update")) if form_grid_field else True

        caption = header.get("hdr_cap") or ""
        if not caption and form_grid_field:
            caption = form_grid_field.get("col_caption") or ""
        caption = clean_caption(caption)

        formatted_columns = []
        for c in columns:
            uitype = (c.get("col_uitype") or "text").strip().lower()
            datatype = c.get("col_datatype")
            c_name = c.get("col_name")
            scale = int(c.get("col_scale") or 0)
            controlexpr = (c.get("col_controlexpr") or "").strip()
            
            is_picker_or_combo = uitype in ("picker", "combobox")
            if controlexpr and not is_picker_or_combo and uitype != "formula":
                uitype = "formula"

            is_formula = (uitype == "formula")
            is_update = bool(c.get("col_update"))
            is_readonly = bool(c.get("col_readonly") or (is_formula and not is_update))
            
            picker_code = controlexpr if uitype == "picker" else None
            picker_hdr_id = self.resolve_hdr_id(db, picker_code) if picker_code else None
            
            col_meta = {
                "name": c_name,
                "caption": clean_caption(c.get("col_cap") or (c_name or "").replace("_", " ").title()),
                "widget": uitype,
                "type": normalize_type(uitype, datatype, c_name, scale),
                "hidden": bool(c.get("col_hide") or False),
                "readonly": is_readonly,
                "update": is_update,
                "scale": scale,
                "width": int(c.get("col_width") or 100),
            }
            if picker_code and uitype == "picker":
                col_meta["pickerCode"] = picker_code
                col_meta["pickerHdrId"] = picker_hdr_id
            if is_formula or (controlexpr and not is_picker_or_combo):
                col_meta["expression"] = controlexpr
            formatted_columns.append(col_meta)

        grid_variables = []
        for v in variables:
            v_name = v.get("var_name")
            v_aggr = (v.get("var_aggr") or "").strip().lower()
            v_col = (v.get("var_controlexpr") or "").strip()
            v_var = {"name": v_name}
            if v_aggr:
                v_var["aggregate"] = v_aggr
                v_var["column"] = v_col
            else:
                v_var["kind"] = "passed"
            grid_variables.append(v_var)

        res = {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": caption,
            "rowKey": row_key,
            "parentField": parent_field or "doc_id",
            "rowNumberField": row_number_field or "trans_idx",
            "canAddRemove": can_add_remove,
            "saveWithForm": save_with_form,
            "columns": formatted_columns,
        }
        if grid_variables:
            res["variables"] = grid_variables
        return res

    def get_grid_meta(self, db: Session, hdr_id: int, user_roles: list[str]) -> dict[str, Any]:
        return self.build_grid_meta(db, hdr_id, user_roles)

    def get_picker_meta(self, db: Session, hdr_id: int, user_roles: list[str]) -> dict[str, Any]:
        header = self.get_screen(db, hdr_id)
        if (header.get("hdr_type") or "").upper() != "PICKER":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="wrong_screen_type", message=f"Expected PICKER, got {header.get('hdr_type')}")

        columns = repo.get_browser_columns(db, hdr_id)
        if not columns and header.get("hdr_expr"):
            columns = repo.infer_columns_from_query(db, header.get("hdr_expr"))

        formatted_columns = []
        for c in columns:
            c_name = c.get("col_name")
            scale = int(c.get("col_scale") or 0)
            formatted_columns.append({
                "name": c_name,
                "caption": clean_caption(c.get("col_cap") or (c_name or "").replace("_", " ").title()),
                "widget": normalize_type(c.get("col_uitype")),
                "type": normalize_type(c.get("col_uitype"), c.get("col_datatype"), c_name, scale),
                "hidden": bool(c.get("col_hide") or False),
            })

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": clean_caption(header.get("hdr_cap")),
            "columns": formatted_columns,
        }

    def process_header_save(
        self,
        db: Session,
        hdr_id: int,
        header_data: dict,
        user: dict,
        is_create: bool = True,
        record_id: Any = None,
    ) -> dict:
        details = repo.get_form_details(db, hdr_id)
        field_defs = {d.get("col_name"): d for d in details if d.get("col_name")}
        
        id_field = "id"
        for d in details:
            if d.get("col_PK") == 1:
                id_field = d.get("col_name")

        context = {
            "_USERID": user.get("id") if user else 1,
            "_USERLOGIN": user.get("login") if user else "system",
            "_CCID": user.get("ccId") if user else 1,
            "_USERLEVEL": ",".join(user.get("roles", [])),
        }

        processed = {}
        for k, v in list(header_data.items()):
            if not is_create and k.lower() == id_field.lower():
                continue
            
            f_def = field_defs.get(k)
            if f_def:
                is_readonly = bool(f_def.get("col_readonly"))
                uitype = (f_def.get("col_uitype") or "").strip().lower()
                is_formula = (uitype == "formula")
                
                if is_readonly and not is_formula:
                    logger.debug(f"Dropped client-supplied readonly field {k} for form {hdr_id}")
                    continue
            
            processed[k] = v

        if is_create:
            for col_name, f_def in field_defs.items():
                if col_name not in processed:
                    is_readonly = bool(f_def.get("col_readonly"))
                    uitype = (f_def.get("col_uitype") or "").strip().lower()
                    is_formula = (uitype == "formula")
                    
                    if not is_readonly or is_formula:
                        default_expr = f_def.get("col_defaultvalue")
                        if default_expr:
                            try:
                                val = evaluate_expression(str(default_expr).strip(), context)
                                if val is not None:
                                    processed[col_name] = val
                            except Exception:
                                pass

        return processed

    def get_form_meta(self, db: Session, hdr_id: int, user_roles: list[str], user: Optional[dict[str, Any]] = None) -> dict[str, Any]:
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
        field_defs = {d.get("col_name"): d for d in details if d.get("col_name")}

        for d in details:
            if d.get("col_PK") == 1:
                id_field = d.get("col_name")
            if d.get("col_PK") in (4, 5) and d.get("col_name"):
                title_fields.append(d.get("col_name"))

        tabs_map: dict[str, list[Any]] = {}
        grids_map: dict[str, Any] = {}

        for d in details:
            uitype = (d.get("col_uitype") or "text").strip().lower()
            if uitype == "grid":
                grid_code = d.get("col_controlexpr")
                grid_hdr_id = self.resolve_hdr_id(db, grid_code)
                if grid_hdr_id:
                    try:
                        grids_map[str(grid_hdr_id)] = self.build_grid_meta(db, grid_hdr_id, user_roles, form_grid_field=d)
                    except Exception:
                        pass

        for d in details:
            tab = clean_caption(d.get("tab_name") or "General")
            if tab not in tabs_map:
                tabs_map[tab] = []
            
            uitype = (d.get("col_uitype") or "text").strip().lower()
            col_name = d.get("col_name") or ""
            datatype = d.get("col_datatype")
            scale = int(d.get("col_scale") or 0)
            is_id_field = col_name and col_name.lower() == id_field.lower()

            field_meta = {
                "name": col_name,
                "caption": clean_caption(d.get("col_caption") or (col_name or "").replace("_", " ").title()),
                "widget": uitype,
                "type": normalize_type(uitype, datatype, col_name, scale),
                "dataType": normalize_type(uitype, datatype, col_name, scale),
                "readonly": bool(d.get("col_readonly")),
                "hidden": bool(d.get("col_hide") or False) or is_id_field,
                "update": bool(d.get("col_update")),
                "inlineWithPrevious": d.get("col_offset") == -1,
            }
            if is_id_field:
                field_meta["isId"] = True

            if uitype == "picker":
                picker_code = d.get("col_controlexpr")
                picker_hdr_id = self.resolve_hdr_id(db, picker_code)
                field_meta["pickerCode"] = picker_code
                field_meta["pickerHdrId"] = picker_hdr_id
            elif uitype == "grid":
                grid_code = d.get("col_controlexpr")
                grid_hdr_id = self.resolve_hdr_id(db, grid_code)
                field_meta["gridCode"] = grid_code
                field_meta["gridHdrId"] = grid_hdr_id
                field_meta["saveWithForm"] = bool(d.get("col_update"))
            elif uitype == "formula":
                field_meta["expression"] = d.get("col_controlexpr")
            elif uitype in ("label", "hr"):
                field_meta["text"] = d.get("col_controlexpr") or d.get("col_caption") or ""
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
                    "name": clean_caption(cmd.get("cmd_name")),
                    "confirm": clean_caption(cmd.get("cmd_message")),
                    "order": cmd.get("cmd_order"),
                })

        form_variables = []
        for v in variables:
            v_name = v.get("var_name")
            expr = (v.get("var_controlexpr") or "").strip()
            
            if expr.lower() in field_defs:
                form_variables.append({
                    "name": v_name,
                    "kind": "field",
                    "from": field_defs[expr.lower()].get("col_name") or expr
                })
                continue
            
            matched = False
            for g_id_str, g_meta in grids_map.items():
                g_vars = g_meta.get("variables", [])
                for gv in g_vars:
                    if (expr and gv["name"].lower() == expr.lower()) or (not expr and gv["name"].lower() == v_name.lower()):
                        form_variables.append({
                            "name": v_name,
                            "kind": "aggregate",
                            "gridHdrId": int(g_id_str),
                            "aggregate": gv.get("aggregate", "sum"),
                            "column": gv.get("column", ""),
                        })
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                logger.warning(f"Unresolved form variable: {v_name} with expr '{expr}' in form hdrId={hdr_id}")
                form_variables.append({
                    "name": v_name,
                    "kind": "unresolved",
                    "from": expr or None,
                })

        return {
            "hdrId": header.get("hdr_id"),
            "code": header.get("hdr_code"),
            "caption": clean_caption(header.get("hdr_cap")),
            "schemaVersion": schema_version,
            "idField": id_field,
            "titleFields": title_fields,
            "docHeader": header.get("doc_header", "").strip() or None,
            "canSave": can_save,
            "journalView": bool(header.get("dtl_journal")),
            "tabs": tabs,
            "variables": form_variables,
            "grids": grids_map,
            "commands": allowed_commands,
        }

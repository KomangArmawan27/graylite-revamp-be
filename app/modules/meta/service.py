import hashlib
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.modules.meta.repository import MetaRepository
from app.shared.types import normalize_type
from app.shared.roles import allowed

repo = MetaRepository()

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
    def get_browser_meta(self, db: Session, code: str, user_roles: List[str]) -> Dict[str, Any]:
        header = repo.get_header_by_code(db, code)
        if not header or header.get("hdr_type") != "BROWSER":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="not_found", message=f"Browser not found: {code}")

        hdr_id = header.get("hdr_id")
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
                    "default": v.get("var_aggr"), # default expr
                    "required": not bool(v.get("var_nullable", True)),
                    "hidden": bool(v.get("var_hide")),
                })

        # Check permissions
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

        return {
            "code": header.get("hdr_code"),
            "caption": header.get("hdr_cap") or "",
            "schemaVersion": schema_version,
            "rowKey": row_key,
            "dateColumn": date_col,
            "detailCode": header.get("dtl_code"),
            "canAdd": can_add,
            "canRemove": can_remove,
            "style": header.get("param1") or "Fit",
            "columns": formatted_columns,
            "filters": filters,
            "layout": layout,
            "commands": allowed_commands,
        }

    def get_form_meta(self, db: Session, code: str, user_roles: List[str]) -> Dict[str, Any]:
        header = repo.get_header_by_code(db, code)
        if not header or header.get("hdr_type") != "DETAIL":
            from app.core.errors import AppError
            raise AppError(status_code=404, code="not_found", message=f"Form not found: {code}")

        hdr_id = header.get("hdr_id")
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
                field_meta["pickerCode"] = d.get("col_controlexpr")
            elif uitype in ("grid",):
                field_meta["gridCode"] = d.get("col_controlexpr")
                field_meta["saveWithForm"] = bool(d.get("col_update"))
            elif uitype == "formula":
                field_meta["expression"] = d.get("col_controlexpr")
            elif uitype == "combobox":
                # parse [1,'Label']
                opts = []
                expr = d.get("col_controlexpr") or ""
                # simple parsing or regex
                field_meta["options"] = opts

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
            "grids": {},
            "defaults": {},
            "commands": allowed_commands,
        }

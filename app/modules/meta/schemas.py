from typing import Any

from pydantic import BaseModel


class ColumnMeta(BaseModel):
    name: str
    caption: str
    type: str
    hidden: bool = False
    scale: int = 0
    width: int = 100

class FilterMeta(BaseModel):
    name: str
    label: str
    type: str
    default: Any | None = None
    required: bool = False
    hidden: bool = False

class BrowserMetaResponse(BaseModel):
    code: str
    caption: str
    schemaVersion: str
    rowKey: str
    dateColumn: str
    detailCode: str | None = None
    canAdd: bool = False
    canRemove: bool = False
    style: str = "Fit"
    columns: list[ColumnMeta]
    filters: list[FilterMeta]
    layout: dict[str, Any]
    commands: list[dict[str, Any]]

class FieldMeta(BaseModel):
    name: str
    caption: str
    widget: str
    dataType: str | None = None
    readonly: bool = False
    hidden: bool = False
    update: bool = False
    inlineWithPrevious: bool = False
    pickerCode: str | None = None
    gridCode: str | None = None
    saveWithForm: bool | None = None
    options: list[dict[str, Any]] | None = None

class TabMeta(BaseModel):
    name: str
    fields: list[FieldMeta]

class FormMetaResponse(BaseModel):
    code: str
    caption: str
    schemaVersion: str
    idField: str
    titleFields: list[str]
    docHeader: str | None = None
    canSave: bool = True
    journalView: bool = False
    tabs: list[TabMeta]
    variables: list[dict[str, Any]]
    grids: dict[str, Any]
    defaults: dict[str, Any]
    commands: list[dict[str, Any]]

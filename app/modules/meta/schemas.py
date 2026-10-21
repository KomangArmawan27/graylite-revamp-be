from typing import Any, Dict, List, Optional
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
    default: Optional[Any] = None
    required: bool = False
    hidden: bool = False

class BrowserMetaResponse(BaseModel):
    code: str
    caption: str
    schemaVersion: str
    rowKey: str
    dateColumn: str
    detailCode: Optional[str] = None
    canAdd: bool = False
    canRemove: bool = False
    style: str = "Fit"
    columns: List[ColumnMeta]
    filters: List[FilterMeta]
    layout: Dict[str, Any]
    commands: List[Dict[str, Any]]

class FieldMeta(BaseModel):
    name: str
    caption: str
    widget: str
    dataType: Optional[str] = None
    readonly: bool = False
    hidden: bool = False
    update: bool = False
    inlineWithPrevious: bool = False
    pickerCode: Optional[str] = None
    gridCode: Optional[str] = None
    saveWithForm: Optional[bool] = None
    options: Optional[List[Dict[str, Any]]] = None

class TabMeta(BaseModel):
    name: str
    fields: List[FieldMeta]

class FormMetaResponse(BaseModel):
    code: str
    caption: str
    schemaVersion: str
    idField: str
    titleFields: List[str]
    docHeader: Optional[str] = None
    canSave: bool = True
    journalView: bool = False
    tabs: List[TabMeta]
    variables: List[Dict[str, Any]]
    grids: Dict[str, Any]
    defaults: Dict[str, Any]
    commands: List[Dict[str, Any]]

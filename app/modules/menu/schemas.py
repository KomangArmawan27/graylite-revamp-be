from pydantic import BaseModel
from typing import List, Optional

class MenuItem(BaseModel):
    hdrId: int
    code: str
    caption: str
    type: str
    module: str
    group: Optional[str] = None
    detailHdrId: Optional[int] = None

class MenuResponse(BaseModel):
    count: int
    items: List[MenuItem]

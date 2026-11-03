
from pydantic import BaseModel


class MenuItem(BaseModel):
    hdrId: int
    code: str
    caption: str
    type: str
    module: str
    group: str | None = None
    detailHdrId: int | None = None

class MenuResponse(BaseModel):
    count: int
    items: list[MenuItem]

from typing import Optional, Any
from pydantic import BaseModel, Field


class CreditNote_sendByWithRender(BaseModel):
    thumbs: Optional[Any] = None
    pages: Optional[int] = None
    docId: Optional[str] = None
    parameters: Optional[Any] = None
    class Config:
        populate_by_name = True
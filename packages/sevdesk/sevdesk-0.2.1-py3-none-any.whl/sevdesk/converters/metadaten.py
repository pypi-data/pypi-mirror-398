from typing import Optional, Any
from pydantic import BaseModel, Field

class Metadaten(BaseModel):
    pages: Optional[int] = None
    docId: Optional[str] = None
    thumbs: Optional[Any] = None
    class Config:
        populate_by_name = True
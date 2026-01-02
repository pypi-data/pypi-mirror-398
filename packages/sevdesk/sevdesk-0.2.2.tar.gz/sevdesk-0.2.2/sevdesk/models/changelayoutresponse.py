from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.metadaten import Metadaten

class ChangeLayoutResponse(BaseModel):
    """Layout model"""

    result: Optional[str] = None
    metadaten: Optional[Metadaten] = None
    class Config:
        populate_by_name = True
from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.error import Error

class ValidationError(BaseModel):
    error: Optional[Error] = None
    class Config:
        populate_by_name = True
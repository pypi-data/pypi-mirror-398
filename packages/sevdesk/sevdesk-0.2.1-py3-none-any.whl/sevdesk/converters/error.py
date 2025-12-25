from typing import Optional
from pydantic import BaseModel, Field

class Error(BaseModel):
    message: Optional[str] = None
    exceptionUUID: Optional[str] = None
    class Config:
        populate_by_name = True
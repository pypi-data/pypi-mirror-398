from typing import Optional
from pydantic import BaseModel, Field

class DiscountDelete(BaseModel):
    id_: Optional[int] = Field(default=None, alias="id")
    objectName: Optional[str] = None
    class Config:
        populate_by_name = True
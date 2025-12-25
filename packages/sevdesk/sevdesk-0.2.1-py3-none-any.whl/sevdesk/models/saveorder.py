from typing import Optional, Any
from pydantic import BaseModel, Field


class SaveOrder(BaseModel):
    order: str
    orderPosSave: Optional[Any] = None
    orderPosDelete: Optional[str] = None
    class Config:
        populate_by_name = True
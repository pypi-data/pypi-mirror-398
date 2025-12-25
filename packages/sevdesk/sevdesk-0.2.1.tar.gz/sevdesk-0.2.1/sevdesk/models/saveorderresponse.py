from typing import Optional, Any
from pydantic import BaseModel, Field


class SaveOrderResponse(BaseModel):
    order: Optional[str] = None
    orderPos: Optional[Any] = None
    class Config:
        populate_by_name = True
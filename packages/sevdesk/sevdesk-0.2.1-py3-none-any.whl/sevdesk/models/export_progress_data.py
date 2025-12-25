from typing import Optional
from pydantic import BaseModel, Field


class Export_Progress_Data(BaseModel):
    current: Optional[int] = Field(default=None, description="Current progress of the export. Export is finished when 'current' reaches 'total' (usually 100)")
    total: Optional[int] = Field(default=None, description="Total value of the export")
    class Config:
        populate_by_name = True
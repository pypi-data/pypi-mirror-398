from typing import Optional
from pydantic import BaseModel, Field


class Export_Job_Download_Info(BaseModel):
    filename: Optional[str] = Field(default=None, description="Current progress of the export. Export is finished when 'current' reaches 'total' (usually 100)")
    link: Optional[str] = Field(default=None, description="Download url of the export file")
    linkExpireDate: Optional[str] = Field(default=None, description="Expire date of the download url")
    class Config:
        populate_by_name = True
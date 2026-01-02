from typing import Optional
from pydantic import BaseModel, Field


class ContactCustomFieldSetting(BaseModel):
    """contact field settings model"""

    name: str = Field(description="name of the contact fields")
    description: Optional[str] = Field(default=None, description="The description of the contact field")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'ContactCustomFieldSetting'.")
    class Config:
        populate_by_name = True
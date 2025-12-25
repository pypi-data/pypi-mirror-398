from typing import Optional
from pydantic import BaseModel, Field


class ContactCustomFieldSettingUpdate(BaseModel):
    """contact fields model"""

    name: Optional[str] = Field(default=None, description="name of the contact fields")
    description: Optional[str] = Field(default=None, description="The description of the contact field")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'ContactCustomFieldSetting'.")
    class Config:
        populate_by_name = True
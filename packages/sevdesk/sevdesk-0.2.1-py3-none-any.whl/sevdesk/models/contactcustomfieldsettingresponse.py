from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class ContactCustomFieldSettingResponse(BaseModel):
    """contact fields model"""

    id_: Optional[str] = Field(default=None, alias="id", description="Id of the contact field")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'ContactCustomFieldSetting'.")
    create: Optional[str] = Field(default=None, description="Date of contact field creation")
    update: Optional[str] = Field(default=None, description="Date of contact field updated")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice belongs. Will be filled automatically")
    name: Optional[str] = Field(default=None, description="name of the contact fields")
    identifier: Optional[str] = Field(default=None, description="Unique identifier for the contact field")
    description: Optional[str] = Field(default=None, description="The description of the contact field")
    class Config:
        populate_by_name = True
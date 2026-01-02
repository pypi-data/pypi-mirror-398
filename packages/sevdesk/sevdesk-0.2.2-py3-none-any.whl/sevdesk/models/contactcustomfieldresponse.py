from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.contact import Contact

class ContactCustomFieldResponse(BaseModel):
    """contact fields model"""

    id_: Optional[str] = Field(default=None, alias="id", description="id of the contact field")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'ContactCustomField'.")
    create: Optional[str] = Field(default=None, description="Date of contact field creation")
    update: Optional[str] = Field(default=None, description="Date of contact field update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which contact field belongs. Will be filled automatically")
    contact: Optional[Contact] = Field(default=None, description="name of the contact")
    contactCustomFieldSetting: Optional[dict] = Field(default=None, description="the contact custom field setting")
    value: Optional[str] = Field(default=None, description="The value of the contact field")
    class Config:
        populate_by_name = True
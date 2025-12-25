from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.contactcustomfieldsetting import ContactCustomFieldSetting

class ContactCustomFieldUpdate(BaseModel):
    """contact fields model"""

    contact: Optional[Contact] = Field(default=None, description="name of the contact")
    contactCustomFieldSetting: Optional[ContactCustomFieldSetting] = Field(default=None, description="name of the contact custom field setting")
    value: Optional[str] = Field(default=None, description="The value of the contact field")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'ContactCustomField'.")
    class Config:
        populate_by_name = True
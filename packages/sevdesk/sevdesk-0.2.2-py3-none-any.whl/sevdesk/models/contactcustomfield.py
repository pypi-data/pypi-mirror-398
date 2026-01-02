from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.contactcustomfieldsetting import ContactCustomFieldSetting

class ContactCustomField(BaseModel):
    """Contact fields model"""

    contact: Contact = Field(description="name of the contact")
    contactCustomFieldSetting: ContactCustomFieldSetting = Field(description="name of the contact custom field setting")
    value: str = Field(description="The value of the contact field")
    objectName: str = Field(description="Internal object name which is 'ContactCustomField'.")
    class Config:
        populate_by_name = True
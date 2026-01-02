from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.key import Key

class CommunicationWayUpdate(BaseModel):
    """Contact communication way model"""

    contact: Optional[Contact] = Field(default=None, description="The contact to which this communication way belongs.")
    type_: Optional[str] = Field(default=None, alias="type", description="Type of the communication way")
    value: Optional[str] = Field(default=None, description="The value of the communication way.<br> For example the phone number, e-mail address or website.")
    key: Optional[Key] = Field(default=None, description="The key of the communication way.<br> Similar to the category of addresses.<br> For all communication way keys please send a GET to /CommunicationWayKey.")
    main: Optional[bool] = Field(default=None, description="Defines whether the communication way is the main communication way for the contact.")
    class Config:
        populate_by_name = True
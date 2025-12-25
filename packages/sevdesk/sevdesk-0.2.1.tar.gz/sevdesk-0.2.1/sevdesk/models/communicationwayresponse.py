from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.key import Key
from sevdesk.converters.sevclient import SevClient

class CommunicationWayResponse(BaseModel):
    """Contact communication way model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The communication way id")
    objectName: Optional[str] = Field(default=None, description="The communication way object name")
    create: Optional[str] = Field(default=None, description="Date of communication way creation")
    update: Optional[str] = Field(default=None, description="Date of last communication way update")
    contact: Optional[Contact] = Field(default=None, description="The contact to which this communication way belongs.")
    type_: Optional[str] = Field(default=None, alias="type", description="Type of the communication way")
    value: Optional[str] = Field(default=None, description="The value of the communication way.<br> For example the phone number, e-mail address or website.")
    key: Optional[Key] = Field(default=None, description="The key of the communication way.<br> Similar to the category of addresses.<br> For all communication way keys please send a GET to /CommunicationWayKey.")
    main: Optional[str] = Field(default=None, description="Defines whether the communication way is the main communication way for the contact.")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which communication way key belongs. Will be filled automatically")
    class Config:
        populate_by_name = True
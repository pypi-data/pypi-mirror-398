from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.contactperson import ContactPerson

class LetterResponse(BaseModel):
    """Response Model für Brief-Operationen"""
    id_: Optional[str] = Field(default=None, alias="id")
    objectName: Optional[str] = None
    additionalInformation: Optional[str] = None
    create: Optional[str] = None
    update: Optional[str] = None
    letterNumber: Optional[str] = None
    contact: Optional[Contact] = None
    letterDate: Optional[str] = None
    header: Optional[str] = None
    sevClient: Optional[SevClient] = None
    status: Optional[str] = None
    contactPerson: Optional[ContactPerson] = None
    addressParentName: Optional[str] = None
    text: Optional[str] = None
    sendDate: Optional[str] = None
    addressParentName2: Optional[str] = None
    address: Optional[str] = None
    sendType: Optional[str] = None
    
    class Config:
        populate_by_name = True
from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.contactperson import ContactPerson

class LetterUpdate(BaseModel):
    """Model zum Aktualisieren eines Briefes"""
    contact: Optional[Contact] = None
    letterDate: Optional[str] = None
    header: Optional[str] = None
    status: Optional[str] = None
    contactPerson: Optional[ContactPerson] = None
    text: Optional[str] = None
    sendDate: Optional[str] = None
    sendType: Optional[str] = None
    objectName: Optional[str] = "Letter"
    address: Optional[str] = None
    
    class Config:
        populate_by_name = True
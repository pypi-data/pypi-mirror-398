from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.addresscountry import AddressCountry

class Letter(BaseModel):
    """Model zum Erstellen eines neuen Briefes"""
    contact: Contact
    letterDate: str
    header: str
    status: str
    contactPerson: ContactPerson
    text: str
    objectName: str = "Letter"
    address: Optional[str] = None
    addressCountry: Optional[AddressCountry] = None
    types: Optional[str] = None
    
    class Config:
        populate_by_name = True
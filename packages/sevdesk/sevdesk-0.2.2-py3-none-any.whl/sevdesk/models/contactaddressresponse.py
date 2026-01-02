from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.country import Country
from sevdesk.converters.category import Category
from sevdesk.converters.sevclient import SevClient

class ContactAddressResponse(BaseModel):
    """ContactAddress model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The contact address id")
    objectName: Optional[str] = Field(default=None, description="The contact address object name")
    create: Optional[str] = Field(default=None, description="Date of contact address creation")
    update: Optional[str] = Field(default=None, description="Date of last contact address update")
    contact: Contact = Field(description="The contact to which this contact address belongs.")
    street: Optional[str] = Field(default=None, description="Street name")
    zip: Optional[str] = Field(default=None, description="Zib code")
    city: Optional[str] = Field(default=None, description="City name")
    country: Country = Field(description="Country of the contact address.<br> For all countries, send a GET to /StaticCountry")
    category: Optional[Category] = Field(default=None, description="Category of the contact address.<br> For all categories, send a GET to /Category?objectType=ContactAddress.")
    name: Optional[str] = Field(default=None, description="Name in address")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which contact address belongs. Will be filled automatically")
    name2: Optional[str] = Field(default=None, description="Second name in address")
    name3: Optional[str] = Field(default=None, description="Third name in address")
    name4: Optional[str] = Field(default=None, description="Fourth name in address")
    class Config:
        populate_by_name = True
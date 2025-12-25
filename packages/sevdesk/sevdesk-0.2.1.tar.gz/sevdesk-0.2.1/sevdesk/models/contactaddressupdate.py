from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.country import Country
from sevdesk.converters.category import Category

class ContactAddressUpdate(BaseModel):
    """ContactAddress model"""

    contact: Optional[Contact] = Field(default=None, description="The contact to which this contact address belongs.")
    street: Optional[str] = Field(default=None, description="Street name")
    zip: Optional[str] = Field(default=None, description="Zib code")
    city: Optional[str] = Field(default=None, description="City name")
    country: Optional[Country] = Field(default=None, description="Country of the contact address.<br> For all countries, send a GET to /StaticCountry")
    category: Optional[Category] = Field(default=None, description="Category of the contact address.<br> For all categories, send a GET to /Category?objectType=ContactAddress.")
    name: Optional[str] = Field(default=None, description="Name in address")
    name2: Optional[str] = Field(default=None, description="Second name in address")
    name3: Optional[str] = Field(default=None, description="Third name in address")
    name4: Optional[str] = Field(default=None, description="Fourth name in address")
    class Config:
        populate_by_name = True
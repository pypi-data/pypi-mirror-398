from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.sevclient import SevClient

class AccountingContactResponse(BaseModel):
    """Accounting contact model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The accounting contact id")
    objectName: Optional[str] = Field(default=None, description="The accounting contact object name")
    create: Optional[str] = Field(default=None, description="Date of accounting contact creation")
    update: Optional[str] = Field(default=None, description="Date of last accounting contact update")
    contact: Optional[Contact] = Field(default=None, description="The contact to which this accounting contact belongs.")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which accounting contact belongs. Will be filled automatically")
    debitorNumber: Optional[str] = Field(default=None, description="Debitor number of the accounting contact.")
    creditorNumber: Optional[str] = Field(default=None, description="Creditor number of the accounting contact.")
    class Config:
        populate_by_name = True
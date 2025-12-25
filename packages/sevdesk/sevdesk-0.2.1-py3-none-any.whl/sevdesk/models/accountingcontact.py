from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact

class AccountingContact(BaseModel):
    """Accounting contact model"""

    contact: Contact = Field(description="The contact to which this accounting contact belongs.")
    debitorNumber: Optional[int] = Field(default=None, description="Debitor number of the accounting contact.")
    creditorNumber: Optional[int] = Field(default=None, description="Creditor number of the accounting contact.")
    class Config:
        populate_by_name = True
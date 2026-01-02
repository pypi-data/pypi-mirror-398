from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class CreateClearingAccountResponse(BaseModel):
    """CheckAccount model. Showing the properties relevant to clearing accounts."""

    id_: Optional[str] = Field(default=None, alias="id", description="The check account id")
    objectName: Optional[str] = Field(default=None, description="The check account object name, always 'CheckAccount'")
    create: Optional[str] = Field(default=None, description="Date of check account creation")
    update: Optional[str] = Field(default=None, description="Date of last check account update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which check account belongs. Will be filled automatically")
    name: Optional[str] = Field(default=None, description="Name of the check account")
    type_: Optional[str] = Field(default=None, alias="type", description="The type of the check account. Clearing accounts are regarded as offline.")
    currency: Optional[str] = Field(default=None, description="The currency of the check account.")
    defaultAccount: Optional[str] = Field(default=None, description="Defines if this check account is the default account.")
    status: Optional[str] = Field(default=None, description="Status of the check account. 0 <-> Archived - 100 <-> Active")
    accountingNumber: Optional[str] = Field(default=None, description="The booking account used for this clearing account.")
    class Config:
        populate_by_name = True
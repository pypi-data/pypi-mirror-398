from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class CreateFileImportAccountResponse(BaseModel):
    """CheckAccount model. Showing the properties relevant to file import accounts."""

    id_: Optional[str] = Field(default=None, alias="id", description="The check account id")
    objectName: Optional[str] = Field(default=None, description="The check account object name, always 'CheckAccount'")
    create: Optional[str] = Field(default=None, description="Date of check account creation")
    update: Optional[str] = Field(default=None, description="Date of last check account update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which check account belongs. Will be filled automatically")
    name: Optional[str] = Field(default=None, description="Name of the check account")
    iban: Optional[str] = Field(default=None, description="The IBAN of the account")
    type_: Optional[str] = Field(default=None, alias="type", description="The type of the check account. Account with a CSV or MT940 import are regarded as online.")
    importType: Optional[str] = Field(default=None, description="Import type, for accounts that are type 'online' but not connected to a data provider. Transactions can be imported by this method on the check account.")
    currency: Optional[str] = Field(default=None, description="The currency of the check account.")
    defaultAccount: Optional[str] = Field(default=None, description="Defines if this check account is the default account.")
    status: Optional[str] = Field(default=None, description="Status of the check account. 0 <-> Archived - 100 <-> Active")
    autoMapTransactions: Optional[str] = Field(default=None, description="Defines if transactions on this account are automatically mapped to invoice and vouchers when imported if possible.")
    accountingNumber: Optional[str] = Field(default=None, description="The booking account used for this bank account, e.g. 1800 in SKR04 and 1200 in SKR03. Must be unique among all your CheckAccounts. Ignore to use a sensible default.")
    class Config:
        populate_by_name = True
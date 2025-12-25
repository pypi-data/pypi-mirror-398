from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class CheckAccountResponse(BaseModel):
    """CheckAccount model. Responsible for the payment accounts."""

    id_: Optional[str] = Field(default=None, alias="id", description="The check account id")
    objectName: Optional[str] = Field(default=None, description="The check account object name")
    create: Optional[str] = Field(default=None, description="Date of check account creation")
    update: Optional[str] = Field(default=None, description="Date of last check account update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which check account belongs. Will be filled automatically")
    name: Optional[str] = Field(default=None, description="Name of the check account")
    iban: Optional[str] = Field(default=None, description="The IBAN of the account")
    type_: Optional[str] = Field(default=None, alias="type", description="The type of the check account. Account with a CSV or MT940 import are regarded as online.")
    importType: Optional[str] = Field(default=None, description="Import type, for accounts that are type 'online' but not connected to a data provider.")
    currency: Optional[str] = Field(default=None, description="The currency of the check account.")
    defaultAccount: Optional[str] = Field(default=None, description="Defines if this check account is the default account.")
    baseAccount: Optional[str] = Field(default=None, description="This will be 1 if the account is your base account that comes with every sevdesk setup.")
    priority: Optional[str] = Field(default=None, description="Defines the sorting of accounts, highest is first.")
    status: Optional[str] = Field(default=None, description="Status of the check account. 0 <-> Archived - 100 <-> Active")
    balance: Optional[str] = Field(default=None, description="The account balance as reported by PayPal or finAPI. Not set for other types of accounts.")
    bankServer: Optional[str] = Field(default=None, description="Bank server of check account, only set if the account is connected to a data provider")
    autoMapTransactions: Optional[str] = Field(default=None, description="Defines if transactions on this account are automatically mapped to invoice and vouchers when imported if possible.")
    autoSyncTransactions: Optional[str] = Field(default=None, description="If this is 1 the account will be automatically updated through PayPal or finAPI. Only applicable for connected online accounts.")
    lastSync: Optional[str] = Field(default=None, description="Timepoint of the last payment import through PayPal or finAPI.")
    accountingNumber: Optional[str] = Field(default=None, description="The booking account used for this account, e.g. 1800 in SKR04 and 1200 in SKR03. Must be unique among all your CheckAccounts.")
    class Config:
        populate_by_name = True
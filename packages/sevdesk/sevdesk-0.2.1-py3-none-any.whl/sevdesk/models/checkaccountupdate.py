from typing import Optional
from pydantic import BaseModel, Field


class CheckAccountUpdate(BaseModel):
    """CheckAccount model. Responsible for the payment accounts."""

    name: Optional[str] = Field(default=None, description="Name of the check account")
    type_: Optional[str] = Field(default=None, alias="type", description="The type of the check account. Account with a CSV or MT940 import are regarded as online.<br> Apart from that, created check accounts over the API need to be offline, as online accounts with an active connection to a bank application can not be managed over the API.")
    importType: Optional[str] = Field(default=None, description="Import type. Transactions can be imported by this method on the check account.")
    currency: Optional[str] = Field(default=None, description="The currency of the check account.")
    defaultAccount: Optional[int] = Field(default=None, description="Defines if this check account is the default account.")
    status: Optional[int] = Field(default=None, description="Status of the check account. 0 <-> Archived - 100 <-> Active")
    autoMapTransactions: Optional[int] = Field(default=None, description="Defines if transactions on this account are automatically mapped to invoice and vouchers when imported if possible.")
    accountingNumber: Optional[str] = Field(default=None, description="The booking account used for this bank account, e.g. 1800 in SKR04 and 1200 in SKR03. Must be unique among all your CheckAccounts. Ignore to use a sensible default.")
    class Config:
        populate_by_name = True
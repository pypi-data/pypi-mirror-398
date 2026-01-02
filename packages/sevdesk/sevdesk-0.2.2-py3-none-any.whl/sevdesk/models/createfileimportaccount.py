from typing import Optional
from pydantic import BaseModel, Field


class CreateFileImportAccount(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the check account")
    importType: Optional[str] = Field(default=None, description="Import type. Transactions can be imported by this method on the check account.")
    accountingNumber: Optional[int] = Field(default=None, description="The booking account used for this bank account, e.g. 1800 in SKR04 and 1200 in SKR03. Must be unique among all your CheckAccounts. Ignore to use a sensible default.")
    iban: Optional[str] = Field(default=None, description="IBAN of the bank account, without spaces")
    class Config:
        populate_by_name = True
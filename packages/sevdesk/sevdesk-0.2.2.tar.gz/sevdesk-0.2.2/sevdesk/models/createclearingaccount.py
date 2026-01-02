from typing import Optional
from pydantic import BaseModel, Field


class CreateClearingAccount(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the check account")
    accountingNumber: Optional[int] = Field(default=None, description="The booking account used for this clearing account, e.g. 3320 in SKR04 and 1723 in SKR03. Must be unique among all your CheckAccounts. Ask your tax consultant what to choose.")
    class Config:
        populate_by_name = True
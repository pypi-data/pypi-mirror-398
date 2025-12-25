from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.checkaccount import CheckAccount
from sevdesk.converters.sourcetransaction import SourceTransaction
from sevdesk.converters.targettransaction import TargetTransaction

class CheckAccountTransactionUpdate(BaseModel):
    """CheckAccountTransaction model. Responsible for the transactions on payment accounts."""

    valueDate: Optional[str] = Field(default=None, description="Date the check account transaction was booked")
    entryDate: Optional[str] = Field(default=None, description="Date the check account transaction was imported")
    paymtPurpose: Optional[str] = Field(default=None, description="the purpose of the transaction")
    amount: Optional[float] = Field(default=None, description="Amount of the transaction")
    payeePayerName: Optional[str] = Field(default=None, description="Name of the payee/payer")
    checkAccount: Optional[CheckAccount] = Field(default=None, description="The check account to which the transaction belongs")
    status: Optional[int] = Field(default=None, description="Status of the check account transaction.<br> 100 <-> Created<br> 200 <-> Linked<br> 300 <-> Private<br> 400 <-> Booked")
    sourceTransaction: Optional[SourceTransaction] = Field(default=None, description="The check account transaction serving as the source of the rebooking")
    targetTransaction: Optional[TargetTransaction] = Field(default=None, description="The check account transaction serving as the target of the rebooking")
    class Config:
        populate_by_name = True
from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.checkaccount import CheckAccount
from sevdesk.converters.sourcetransaction import SourceTransaction
from sevdesk.converters.targettransaction import TargetTransaction

class CheckAccountTransaction(BaseModel):
    """CheckAccountTransaction model. Responsible for the transactions on payment accounts."""

    id_: Optional[int] = Field(default=None, alias="id", description="The check account transaction id")
    objectName: Optional[str] = Field(default=None, description="The check account transaction object name")
    create: Optional[str] = Field(default=None, description="Date of check account transaction creation")
    update: Optional[str] = Field(default=None, description="Date of last check account transaction update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which check account transaction belongs. Will be filled automatically")
    valueDate: str = Field(description="Date the check account transaction was booked")
    entryDate: Optional[str] = Field(default=None, description="Date the check account transaction was imported")
    paymtPurpose: Optional[str] = Field(default=None, description="The purpose of the transaction")
    amount: float = Field(description="Amount of the transaction")
    payeePayerName: Optional[str] = Field(description="Name of the other party")
    payeePayerAcctNo: Optional[str] = Field(default=None, description="IBAN or account number of the other party")
    payeePayerBankCode: Optional[str] = Field(default=None, description="BIC or bank code of the other party")
    checkAccount: CheckAccount = Field(description="The check account to which the transaction belongs")
    status: int = Field(description="Status of the check account transaction.<br> 100 <-> Created<br> 200 <-> Linked<br> 300 <-> Private<br> 400 <-> Booked")
    sourceTransaction: Optional[SourceTransaction] = Field(default=None, description="The check account transaction serving as the source of the rebooking")
    targetTransaction: Optional[TargetTransaction] = Field(default=None, description="The check account transaction serving as the target of the rebooking")
    class Config:
        populate_by_name = True
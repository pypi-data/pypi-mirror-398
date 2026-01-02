from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.checkaccount import CheckAccount
from sevdesk.converters.sourcetransaction import SourceTransaction
from sevdesk.converters.targettransaction import TargetTransaction

class CheckAccountTransactionResponse(BaseModel):
    """CheckAccountTransaction model. Responsible for the transactions on payment accounts."""

    id_: Optional[str] = Field(default=None, alias="id", description="The check account transaction id")
    objectName: Optional[str] = Field(default=None, description="The check account transaction object name")
    create: Optional[str] = Field(default=None, description="Date of check account transaction creation")
    update: Optional[str] = Field(default=None, description="Date of last check account transaction update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which check account transaction belongs. Will be filled automatically")
    valueDate: Optional[str] = Field(default=None, description="Date the check account transaction was imported")
    entryDate: Optional[str] = Field(default=None, description="Date the check account transaction was booked")
    paymtPurpose: Optional[str] = Field(default=None, description="The purpose of the transaction")
    amount: Optional[str] = Field(default=None, description="Amount of the transaction")
    payeePayerName: Optional[str] = Field(default=None, description="Name of the other party")
    payeePayerAcctNo: Optional[str] = Field(default=None, description="IBAN or account number of the other party")
    payeePayerBankCode: Optional[str] = Field(default=None, description="BIC or bank code of the other party")
    gvCode: Optional[str] = Field(default=None, description="ZKA business transaction code. This can be given for finAPI accounts.")
    entryText: Optional[str] = Field(default=None, description="Transaction type, according to the bank. This can be given for finAPI accounts.")
    primaNotaNo: Optional[str] = Field(default=None, description="Transaction primanota. This can be given for finAPI accounts.")
    checkAccount: Optional[CheckAccount] = Field(default=None, description="The check account to which the transaction belongs")
    status: Optional[str] = Field(default=None, description="Status of the check account transaction.<br> 100 <-> Created<br> 200 <-> Linked<br> 300 <-> Private<br> 350 <-> Auto-booked without user confirmation<br>400 <-> Booked")
    sourceTransaction: Optional[SourceTransaction] = Field(default=None, description="The check account transaction serving as the source of a money transit")
    targetTransaction: Optional[TargetTransaction] = Field(default=None, description="The check account transaction serving as the target of a money transit")
    enshrined: Optional[str] = Field(default=None, description="Timepoint when the transaction was enshrined.")
    class Config:
        populate_by_name = True
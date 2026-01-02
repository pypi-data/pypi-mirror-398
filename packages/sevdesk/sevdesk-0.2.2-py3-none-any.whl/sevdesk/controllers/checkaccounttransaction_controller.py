from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.checkaccounttransaction import CheckAccountTransaction
from sevdesk.models.checkaccounttransactionresponse import CheckAccountTransactionResponse
from sevdesk.models.checkaccounttransactionupdate import CheckAccountTransactionUpdate

class CheckAccountTransactionController(BaseController):

    @BaseController.get("/CheckAccountTransaction")
    def getTransactions(self, checkAccount_id: Optional[int] = None, checkAccount_objectName: Optional[str] = None, endDate: Optional[str] = None, isBooked: Optional[bool] = None, onlyCredit: Optional[bool] = None, onlyDebit: Optional[bool] = None, payeePayerName: Optional[str] = None, paymtPurpose: Optional[str] = None, startDate: Optional[str] = None) -> list[CheckAccountTransactionResponse]:
        """Retrieve transactions"""
        return (yield)

    @BaseController.post("/CheckAccountTransaction")
    def createTransaction(self, body: CheckAccountTransaction) -> CheckAccountTransactionResponse:
        """Create a new transaction"""
        return (yield)

    @BaseController.get("/CheckAccountTransaction/{checkAccountTransactionId}")
    def getCheckAccountTransactionById(self, checkAccountTransactionId: int) -> list[CheckAccountTransactionResponse]:
        """Find check account transaction by ID"""
        return (yield)

    @BaseController.put("/CheckAccountTransaction/{checkAccountTransactionId}")
    def updateCheckAccountTransaction(self, checkAccountTransactionId: int, body: CheckAccountTransactionUpdate) -> CheckAccountTransactionResponse:
        """Update an existing check account transaction"""
        return (yield)

    @BaseController.delete("/CheckAccountTransaction/{checkAccountTransactionId}")
    def deleteCheckAccountTransaction(self, checkAccountTransactionId: int):
        """Deletes a check account transaction"""
        return (yield)

    @BaseController.put("/CheckAccountTransaction/{checkAccountTransactionId}/enshrine")
    def checkAccountTransactionEnshrine(self, checkAccountTransactionId: int):
        """Enshrine"""
        return (yield)


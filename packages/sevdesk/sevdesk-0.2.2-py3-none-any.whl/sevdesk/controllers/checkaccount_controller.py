from sevdesk.base.basecontroller import BaseController
from sevdesk.models.checkaccountresponse import CheckAccountResponse
from sevdesk.models.checkaccountupdate import CheckAccountUpdate
from sevdesk.models.createclearingaccount import CreateClearingAccount
from sevdesk.models.createclearingaccountresponse import CreateClearingAccountResponse
from sevdesk.models.createfileimportaccount import CreateFileImportAccount
from sevdesk.models.createfileimportaccountresponse import CreateFileImportAccountResponse

class CheckAccountController(BaseController):

    @BaseController.get("/CheckAccount")
    def getCheckAccounts(self) -> list[CheckAccountResponse]:
        """Retrieve check accounts"""
        return (yield)

    @BaseController.post("/CheckAccount/Factory/fileImportAccount")
    def createFileImportAccount(self, body: CreateFileImportAccount) -> CreateFileImportAccountResponse:
        """Create a new file import account"""
        return (yield)

    @BaseController.post("/CheckAccount/Factory/clearingAccount")
    def createClearingAccount(self, body: CreateClearingAccount) -> CreateClearingAccountResponse:
        """Create a new clearing account"""
        return (yield)

    @BaseController.get("/CheckAccount/{checkAccountId}")
    def getCheckAccountById(self, checkAccountId: int) -> list[CheckAccountResponse]:
        """Find check account by ID"""
        return (yield)

    @BaseController.put("/CheckAccount/{checkAccountId}")
    def updateCheckAccount(self, checkAccountId: int, body: CheckAccountUpdate) -> CheckAccountResponse:
        """Update an existing check account"""
        return (yield)

    @BaseController.delete("/CheckAccount/{checkAccountId}")
    def deleteCheckAccount(self, checkAccountId: int):
        """Deletes a check account"""
        return (yield)

    @BaseController.get("/CheckAccount/{checkAccountId}/getBalanceAtDate")
    def getBalanceAtDate(self, checkAccountId: int, date: str):
        """Get the balance at a given date"""
        return (yield)


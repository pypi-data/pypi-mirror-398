from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.accountingcontact import AccountingContact
from sevdesk.models.accountingcontactresponse import AccountingContactResponse
from sevdesk.models.accountingcontactupdate import AccountingContactUpdate

class AccountingContactController(BaseController):

    @BaseController.get("/AccountingContact")
    def getAccountingContact(self, contact_id: Optional[str] = None, contact_objectName: Optional[str] = None) -> list[AccountingContactResponse]:
        """Retrieve accounting contact"""
        return (yield)

    @BaseController.post("/AccountingContact")
    def createAccountingContact(self, body: AccountingContact) -> AccountingContactResponse:
        """Create a new accounting contact"""
        return (yield)

    @BaseController.get("/AccountingContact/{accountingContactId}")
    def getAccountingContactById(self, accountingContactId: int) -> list[AccountingContactResponse]:
        """Find accounting contact by ID"""
        return (yield)

    @BaseController.put("/AccountingContact/{accountingContactId}")
    def updateAccountingContact(self, accountingContactId: int, body: AccountingContactUpdate) -> AccountingContactResponse:
        """Update an existing accounting contact"""
        return (yield)

    @BaseController.delete("/AccountingContact/{accountingContactId}")
    def deleteAccountingContact(self, accountingContactId: int):
        """Deletes an accounting contact"""
        return (yield)


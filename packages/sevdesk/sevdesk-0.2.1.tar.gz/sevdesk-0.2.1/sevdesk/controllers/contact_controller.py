from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.contact import Contact
from sevdesk.models.contactresponse import ContactResponse
from sevdesk.models.contactupdate import ContactUpdate

class ContactController(BaseController):

    @BaseController.get("/Contact/Factory/getNextCustomerNumber")
    def getNextCustomerNumber(self):
        """Get next free customer number"""
        return (yield)

    @BaseController.get("/Contact/Factory/findContactsByCustomFieldValue")
    def findContactsByCustomFieldValue(self, customFieldName: str, value: str, customFieldSetting_id: Optional[str] = None, customFieldSetting_objectName: Optional[str] = None) -> list[ContactResponse]:
        """Find contacts by custom field value"""
        return (yield)

    @BaseController.get("/Contact/Mapper/checkCustomerNumberAvailability")
    def contactCustomerNumberAvailabilityCheck(self, customerNumber: Optional[str] = None):
        """Check if a customer number is available"""
        return (yield)

    @BaseController.get("/Contact")
    def getContacts(self, customerNumber: Optional[str] = None, depth: Optional[str] = None) -> list[ContactResponse]:
        """Retrieve contacts"""
        return (yield)

    @BaseController.post("/Contact")
    def createContact(self, body: Contact) -> ContactResponse:
        """Create a new contact"""
        return (yield)

    @BaseController.get("/Contact/{contactId}")
    def getContactById(self, contactId: int) -> list[ContactResponse]:
        """Find contact by ID"""
        return (yield)

    @BaseController.put("/Contact/{contactId}")
    def updateContact(self, contactId: int, body: ContactUpdate) -> ContactResponse:
        """Update a existing contact"""
        return (yield)

    @BaseController.delete("/Contact/{contactId}")
    def deleteContact(self, contactId: int):
        """Deletes a contact"""
        return (yield)

    @BaseController.get("/Contact/{contactId}/getTabsItemCount")
    def getContactTabsItemCountById(self, contactId: int):
        """Get number of all items"""
        return (yield)


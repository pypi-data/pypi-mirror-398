from sevdesk.base.basecontroller import BaseController
from sevdesk.models.contactaddress import ContactAddress
from sevdesk.models.contactaddressresponse import ContactAddressResponse
from sevdesk.models.contactaddressupdate import ContactAddressUpdate

class ContactAddressController(BaseController):

    @BaseController.post("/ContactAddress")
    def createContactAddress(self, body: ContactAddress) -> ContactAddressResponse:
        """Create a new contact address"""
        return (yield)

    @BaseController.get("/ContactAddress")
    def getContactAddresses(self) -> list[ContactAddressResponse]:
        """Retrieve contact addresses"""
        return (yield)

    @BaseController.get("/ContactAddress/{contactAddressId}")
    def contactAddressId(self, contactAddressId: int) -> list[ContactAddressResponse]:
        """Find contact address by ID"""
        return (yield)

    @BaseController.put("/ContactAddress/{contactAddressId}")
    def updateContactAddress(self, contactAddressId: int, body: ContactAddressUpdate) -> ContactAddressResponse:
        """update a existing contact address"""
        return (yield)

    @BaseController.delete("/ContactAddress/{contactAddressId}")
    def deleteContactAddress(self, contactAddressId: int):
        """Deletes a contact address"""
        return (yield)


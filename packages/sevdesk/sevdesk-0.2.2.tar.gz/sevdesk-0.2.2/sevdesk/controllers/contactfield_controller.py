from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.contactcustomfield import ContactCustomField
from sevdesk.models.contactcustomfieldresponse import ContactCustomFieldResponse
from sevdesk.models.contactcustomfieldsetting import ContactCustomFieldSetting
from sevdesk.models.contactcustomfieldsettingresponse import ContactCustomFieldSettingResponse
from sevdesk.models.contactcustomfieldsettingupdate import ContactCustomFieldSettingUpdate
from sevdesk.models.contactcustomfieldupdate import ContactCustomFieldUpdate
from sevdesk.models.textparser_fetchdictionaryentriesbytype_response import Textparser_fetchDictionaryEntriesByType_response

class ContactFieldController(BaseController):

    @BaseController.get("/Textparser/fetchDictionaryEntriesByType")
    def getPlaceholder(self, objectName: str, subObjectName: Optional[str] = None) -> list[Textparser_fetchDictionaryEntriesByType_response]:
        """Retrieve Placeholders"""
        return (yield)

    @BaseController.get("/ContactCustomField")
    def getContactFields(self) -> list[ContactCustomFieldResponse]:
        """Retrieve contact fields"""
        return (yield)

    @BaseController.post("/ContactCustomField")
    def createContactField(self, body: ContactCustomField) -> ContactCustomFieldResponse:
        """Create contact field"""
        return (yield)

    @BaseController.get("/ContactCustomField/{contactCustomFieldId}")
    def getContactFieldsById(self, contactCustomFieldId: float) -> list[ContactCustomFieldResponse]:
        """Retrieve contact fields"""
        return (yield)

    @BaseController.put("/ContactCustomField/{contactCustomFieldId}")
    def updateContactfield(self, contactCustomFieldId: float, body: ContactCustomFieldUpdate) -> ContactCustomFieldResponse:
        """Update a contact field"""
        return (yield)

    @BaseController.delete("/ContactCustomField/{contactCustomFieldId}")
    def deleteContactCustomFieldId(self, contactCustomFieldId: int):
        """delete a contact field"""
        return (yield)

    @BaseController.get("/ContactCustomFieldSetting")
    def getContactFieldSettings(self) -> list[ContactCustomFieldSettingResponse]:
        """Retrieve contact field settings"""
        return (yield)

    @BaseController.post("/ContactCustomFieldSetting")
    def createContactFieldSetting(self, body: ContactCustomFieldSetting) -> list[ContactCustomFieldSettingResponse]:
        """Create contact field setting"""
        return (yield)

    @BaseController.get("/ContactCustomFieldSetting/{contactCustomFieldSettingId}")
    def getContactFieldSettingById(self, contactCustomFieldSettingId: int) -> list[ContactCustomFieldSettingResponse]:
        """Find contact field setting by ID"""
        return (yield)

    @BaseController.put("/ContactCustomFieldSetting/{contactCustomFieldSettingId}")
    def updateContactFieldSetting(self, contactCustomFieldSettingId: int, body: ContactCustomFieldSettingUpdate) -> ContactCustomFieldSettingResponse:
        """Update contact field setting"""
        return (yield)

    @BaseController.delete("/ContactCustomFieldSetting/{contactCustomFieldSettingId}")
    def deleteContactFieldSetting(self, contactCustomFieldSettingId: int):
        """Deletes a contact field setting"""
        return (yield)

    @BaseController.get("/ContactCustomFieldSetting/{contactCustomFieldSettingId}/getReferenceCount")
    def getReferenceCount(self, contactCustomFieldSettingId: int):
        """Receive count reference"""
        return (yield)


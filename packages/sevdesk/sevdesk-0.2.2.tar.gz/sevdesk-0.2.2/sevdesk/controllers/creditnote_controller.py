from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.creditnoteresponse import CreditNoteResponse
from sevdesk.models.creditnoteupdate import CreditNoteUpdate
from sevdesk.models.creditnote_mailresponse import CreditNote_mailResponse
from sevdesk.models.creditnote_sendbywithrender import CreditNote_sendByWithRender
from sevdesk.models.savecreditnote import SaveCreditNote
from sevdesk.models.savecreditnoteresponse import SaveCreditNoteResponse

class CreditNoteController(BaseController):

    @BaseController.get("/CreditNote")
    def getCreditNotes(self, contact_id: Optional[int] = None, contact_objectName: Optional[str] = None, creditNoteNumber: Optional[str] = None, endDate: Optional[int] = None, startDate: Optional[int] = None, status: Optional[str] = None) -> list[CreditNoteResponse]:
        """Retrieve CreditNote"""
        return (yield)

    @BaseController.post("/CreditNote/Factory/saveCreditNote")
    def createcreditNote(self, body: SaveCreditNote) -> SaveCreditNoteResponse:
        """Create a new creditNote"""
        return (yield)

    @BaseController.post("/CreditNote/Factory/createFromInvoice")
    def createCreditNoteFromInvoice(self):
        """Creates a new creditNote from an invoice"""
        return (yield)

    @BaseController.post("/CreditNote/Factory/createFromVoucher")
    def createCreditNoteFromVoucher(self):
        """Creates a new creditNote from a voucher"""
        return (yield)

    @BaseController.get("/CreditNote/{creditNoteId}")
    def getcreditNoteById(self, creditNoteId: int) -> list[CreditNoteResponse]:
        """Find creditNote by ID"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}")
    def updatecreditNote(self, creditNoteId: int, body: CreditNoteUpdate) -> CreditNoteResponse:
        """Update an existing creditNote"""
        return (yield)

    @BaseController.delete("/CreditNote/{creditNoteId}")
    def deletecreditNote(self, creditNoteId: int):
        """Deletes an creditNote"""
        return (yield)

    @BaseController.get("/CreditNote/{creditNoteId}/sendByWithRender")
    def sendCreditNoteByPrinting(self, creditNoteId: int, sendType: str) -> CreditNote_sendByWithRender:
        """Send credit note by printing"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/sendBy")
    def creditNoteSendBy(self, creditNoteId: int) -> CreditNoteResponse:
        """Mark credit note as sent"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/enshrine")
    def creditNoteEnshrine(self, creditNoteId: int):
        """Enshrine"""
        return (yield)

    @BaseController.get("/CreditNote/{creditNoteId}/getPdf")
    def creditNoteGetPdf(self, creditNoteId: int, download: Optional[bool] = None, preventSendBy: Optional[bool] = None):
        """Retrieve pdf document of a credit note"""
        return (yield)

    @BaseController.post("/CreditNote/{creditNoteId}/sendViaEmail")
    def sendCreditNoteViaEMail(self, creditNoteId: int) -> list[CreditNote_mailResponse]:
        """Send credit note via email"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/bookAmount")
    def bookCreditNote(self, creditNoteId: int):
        """Book a credit note"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/resetToOpen")
    def creditNoteResetToOpen(self, creditNoteId: int):
        """Reset status to open"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/resetToDraft")
    def creditNoteResetToDraft(self, creditNoteId: int):
        """Reset status to draft"""
        return (yield)


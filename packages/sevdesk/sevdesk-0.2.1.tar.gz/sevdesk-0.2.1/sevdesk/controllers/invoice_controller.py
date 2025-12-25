from sevdesk.base.basecontroller import BaseController
from typing import Optional, Any
from sevdesk.models.createinvoicefromorder import CreateInvoiceFromOrder
from sevdesk.models.email import Email
from sevdesk.models.invoiceposresponse import InvoicePosResponse
from sevdesk.models.invoiceresponse import InvoiceResponse
from sevdesk.models.saveinvoice import SaveInvoice
from sevdesk.models.saveinvoiceresponse import SaveInvoiceResponse

class InvoiceController(BaseController):

    @BaseController.get("/Invoice")
    def getInvoices(self, contact_id: Optional[int] = None, contact_objectName: Optional[str] = None, endDate: Optional[int] = None, invoiceNumber: Optional[str] = None, startDate: Optional[int] = None, status: Optional[float] = None) -> list[InvoiceResponse]:
        """Retrieve invoices"""
        return (yield)

    @BaseController.post("/Invoice/Factory/saveInvoice")
    def createInvoiceByFactory(self, body: SaveInvoice) -> SaveInvoiceResponse:
        """Create a new invoice"""
        return (yield)

    @BaseController.get("/Invoice/{invoiceId}")
    def getInvoiceById(self, invoiceId: int) -> list[InvoiceResponse]:
        """Find invoice by ID"""
        return (yield)

    @BaseController.get("/Invoice/{invoiceId}/getPositions")
    def getInvoicePositionsById(self, invoiceId: int, embed: Optional[Any] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> list[InvoicePosResponse]:
        """Find invoice positions"""
        return (yield)

    @BaseController.post("/Invoice/Factory/createInvoiceFromOrder")
    def createInvoiceFromOrder(self, body: CreateInvoiceFromOrder) -> InvoiceResponse:
        """Create invoice from order"""
        return (yield)

    @BaseController.post("/Invoice/Factory/createInvoiceReminder")
    def createInvoiceReminder(self, invoice_id: int, invoice_objectName: str) -> InvoiceResponse:
        """Create invoice reminder"""
        return (yield)

    @BaseController.get("/Invoice/{invoiceId}/getIsPartiallyPaid")
    def getIsInvoicePartiallyPaid(self, invoiceId: int):
        """Check if an invoice is already partially paid"""
        return (yield)

    @BaseController.post("/Invoice/{invoiceId}/cancelInvoice")
    def cancelInvoice(self, invoiceId: int) -> InvoiceResponse:
        """Cancel an invoice / Create cancellation invoice"""
        return (yield)

    @BaseController.post("/Invoice/{invoiceId}/render")
    def invoiceRender(self, invoiceId: int):
        """Render the pdf document of an invoice"""
        return (yield)

    @BaseController.post("/Invoice/{invoiceId}/sendViaEmail")
    def sendInvoiceViaEMail(self, invoiceId: int) -> Email:
        """Send invoice via email"""
        return (yield)

    @BaseController.get("/Invoice/{invoiceId}/getPdf")
    def invoiceGetPdf(self, invoiceId: int, download: Optional[bool] = None, preventSendBy: Optional[bool] = None):
        """Retrieve pdf document of an invoice"""
        return (yield)

    @BaseController.get("/Invoice/{invoiceId}/getXml")
    def invoiceGetXml(self, invoiceId: int):
        """Retrieve XML of an e-invoice"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/sendBy")
    def invoiceSendBy(self, invoiceId: int) -> InvoiceResponse:
        """Mark invoice as sent"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/enshrine")
    def invoiceEnshrine(self, invoiceId: int):
        """Enshrine"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/bookAmount")
    def bookInvoice(self, invoiceId: int):
        """Book an invoice"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/resetToOpen")
    def invoiceResetToOpen(self, invoiceId: int):
        """Reset status to open"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/resetToDraft")
    def invoiceResetToDraft(self, invoiceId: int):
        """Reset status to draft"""
        return (yield)


from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.changelayout import ChangeLayout
from sevdesk.models.changelayoutresponse import ChangeLayoutResponse

class LayoutController(BaseController):

    @BaseController.get("/DocServer/getLetterpapersWithThumb")
    def getLetterpapersWithThumb(self):
        """Retrieve letterpapers"""
        return (yield)

    @BaseController.get("/DocServer/getTemplatesWithThumb")
    def getTemplates(self, type_: Optional[str] = None):
        """Retrieve templates"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/changeParameter")
    def updateInvoiceTemplate(self, invoiceId: int, body: ChangeLayout) -> ChangeLayoutResponse:
        """Update an invoice template"""
        return (yield)

    @BaseController.put("/Order/{orderId}/changeParameter")
    def updateOrderTemplate(self, orderId: int, body: ChangeLayout) -> ChangeLayoutResponse:
        """Update an order template"""
        return (yield)

    @BaseController.put("/CreditNote/{creditNoteId}/changeParameter")
    def updateCreditNoteTemplate(self, creditNoteId: int, body: ChangeLayout) -> ChangeLayoutResponse:
        """Update an of credit note template"""
        return (yield)


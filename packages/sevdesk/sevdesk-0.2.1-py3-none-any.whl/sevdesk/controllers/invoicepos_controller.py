from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.invoiceposresponse import InvoicePosResponse

class InvoicePosController(BaseController):

    @BaseController.get("/InvoicePos")
    def getInvoicePos(self, id_: Optional[float] = None, invoice_id: Optional[float] = None, invoice_objectName: Optional[str] = None, part_id: Optional[float] = None, part_objectName: Optional[str] = None) -> list[InvoicePosResponse]:
        """Retrieve InvoicePos"""
        return (yield)


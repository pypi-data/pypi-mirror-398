"""
Undocumented InvoicePos Controller

POST /InvoicePos ist nicht in der OpenAPI-Spec dokumentiert,
funktioniert aber zum Erstellen von Rechnungspositionen.
"""

from sevdesk.base.basecontroller import BaseController
from sevdesk.models.invoicepos import InvoicePos
from sevdesk.models.invoiceposresponse import InvoicePosResponse


class InvoicePosController(BaseController):
    """Controller fuer Rechnungspositionen (undokumentierte Endpoints)."""

    @BaseController.post("/InvoicePos")
    def createInvoicePos(self, body: InvoicePos) -> InvoicePosResponse:
        """
        Erstellt eine Rechnungsposition.

        Args:
            body: InvoicePos-Model mit Positionsdaten

        Returns:
            InvoicePosResponse mit der gespeicherten Position
        """
        return (yield)

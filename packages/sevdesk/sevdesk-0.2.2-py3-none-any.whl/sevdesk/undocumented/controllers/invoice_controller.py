"""
Undocumented Invoice Controller

Erweitert die Standard-Invoice-Funktionen mit nicht-offiziell dokumentierten Features.
"""

from sevdesk.base.basecontroller import BaseController
from sevdesk.controllers.invoice_controller import InvoiceController as BaseInvoiceController
from sevdesk.models.invoice import Invoice
from sevdesk.models.invoiceresponse import InvoiceResponse


class InvoiceController(BaseInvoiceController):
    """
    Erweiterte Invoice-Controller mit zusaetzlichen Funktionen.

    Zusaetzliche Methoden:
    - createInvoice() - Direktes Erstellen von Rechnungen (nicht nur Factory)
    """

    @BaseController.post("/Invoice")
    def createInvoice(self, body: Invoice) -> InvoiceResponse:
        """
        Erstellt eine Rechnung direkt via POST /Invoice.

        Dies ist nicht offiziell dokumentiert, aber funktioniert und ist
        einfacher als die Factory-Methode.

        Args:
            body: Invoice-Model mit allen Rechnungsdaten

        Returns:
            InvoiceResponse mit der gespeicherten Rechnung
        """
        return (yield)

    @BaseController.delete("/Invoice/{invoiceId}")
    def deleteInvoice(self, invoiceId: int):
        """Delete an invoice (only draft invoices can be deleted)"""
        return (yield)

    @BaseController.put("/Invoice/{invoiceId}/sendBy")
    def invoiceSendByWithType(self, invoiceId: int, sendType: str = "VPR") -> InvoiceResponse:
        """
        Mark invoice as sent with sendType parameter.

        Die offizielle API benoetigt sendType, aber der generierte Controller hat diesen nicht.

        Args:
            invoiceId: ID der Rechnung
            sendType: Art des Versands:
                - "VPR" = Versand per Post (default)
                - "VP" = Portal
                - "VPDF" = PDF
                - "VM" = E-Mail

        Returns:
            InvoiceResponse mit aktualisierter Rechnung
        """
        return (yield)

"""
Undocumented Order Controller

Erweitert die Standard-Order-Funktionen mit nicht-offiziell dokumentierten Features.
"""

from sevdesk.base.basecontroller import BaseController
from sevdesk.controllers.order_controller import OrderController as BaseOrderController
from sevdesk.models.order import Order
from sevdesk.models.orderresponse import OrderResponse


class OrderController(BaseOrderController):
    """
    Erweiterte Order-Controller mit zusaetzlichen Funktionen.

    Zusaetzliche Methoden:
    - createOrderDirect() - Direktes Erstellen von Angeboten/Auftraegen (nicht Factory)
    """

    @BaseController.post("/Order")
    def createOrderDirect(self, body: Order) -> OrderResponse:
        """
        Erstellt ein Angebot/Auftrag direkt via POST /Order.

        Dies ist nicht offiziell dokumentiert, aber funktioniert und ist
        einfacher als die Factory-Methode (die fehlerhafte SaveOrder-Model hat).

        Args:
            body: Order-Model mit allen Daten

        Returns:
            OrderResponse mit dem gespeicherten Angebot/Auftrag
        """
        return (yield)

"""
Undocumented OrderPos Controller

POST /OrderPos ist nicht in der OpenAPI-Spec dokumentiert,
funktioniert aber zum Erstellen von Auftragspositionen.
"""

from sevdesk.base.basecontroller import BaseController
from sevdesk.models.orderpos import OrderPos
from sevdesk.models.orderposresponse import OrderPosResponse


class OrderPosController(BaseController):
    """Controller fuer Auftragspositionen (undokumentierte Endpoints)."""

    @BaseController.post("/OrderPos")
    def createOrderPos(self, body: OrderPos) -> OrderPosResponse:
        """
        Erstellt eine Auftragsposition.

        Args:
            body: OrderPos-Model mit Positionsdaten

        Returns:
            OrderPosResponse mit der gespeicherten Position
        """
        return (yield)

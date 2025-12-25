from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.orderposresponse import OrderPosResponse
from sevdesk.models.orderposupdate import OrderPosUpdate

class OrderPosController(BaseController):

    @BaseController.get("/OrderPos")
    def getOrderPositions(self, order_id: Optional[int] = None, order_objectName: Optional[str] = None) -> list[OrderPosResponse]:
        """Retrieve order positions"""
        return (yield)

    @BaseController.get("/OrderPos/{orderPosId}")
    def getOrderPositionById(self, orderPosId: int) -> list[OrderPosResponse]:
        """Find order position by ID"""
        return (yield)

    @BaseController.put("/OrderPos/{orderPosId}")
    def updateOrderPosition(self, orderPosId: int, body: OrderPosUpdate) -> OrderPosResponse:
        """Update an existing order position"""
        return (yield)

    @BaseController.delete("/OrderPos/{orderPosId}")
    def deleteOrderPos(self, orderPosId: int):
        """Deletes an order Position"""
        return (yield)


from sevdesk.base.basecontroller import BaseController
from typing import Optional, Any
from sevdesk.models.createpackinglistfromorder import CreatePackingListFromOrder
from sevdesk.models.discount import Discount
from sevdesk.models.emailorder import EmailOrder
from sevdesk.models.orderposresponse import OrderPosResponse
from sevdesk.models.orderresponse import OrderResponse
from sevdesk.models.orderupdate import OrderUpdate
from sevdesk.models.saveorder import SaveOrder
from sevdesk.models.saveorderresponse import SaveOrderResponse

class OrderController(BaseController):

    @BaseController.get("/Order")
    def getOrders(self, contact_id: Optional[int] = None, contact_objectName: Optional[str] = None, endDate: Optional[int] = None, orderNumber: Optional[str] = None, startDate: Optional[int] = None, status: Optional[int] = None) -> list[OrderResponse]:
        """Retrieve orders"""
        return (yield)

    @BaseController.post("/Order/Factory/saveOrder")
    def createOrder(self, body: SaveOrder) -> SaveOrderResponse:
        """Create a new order"""
        return (yield)

    @BaseController.get("/Order/{orderId}")
    def getOrderById(self, orderId: int) -> list[OrderResponse]:
        """Find order by ID"""
        return (yield)

    @BaseController.put("/Order/{orderId}")
    def updateOrder(self, orderId: int, body: OrderUpdate) -> OrderResponse:
        """Update an existing order"""
        return (yield)

    @BaseController.delete("/Order/{orderId}")
    def deleteOrder(self, orderId: int):
        """Deletes an order"""
        return (yield)

    @BaseController.get("/Order/{orderId}/getPositions")
    def getOrderPositionsById(self, orderId: int, embed: Optional[Any] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> list[OrderPosResponse]:
        """Find order positions"""
        return (yield)

    @BaseController.get("/Order/{orderId}/getDiscounts")
    def getDiscounts(self, orderId: int, embed: Optional[Any] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Discount]:
        """Find order discounts"""
        return (yield)

    @BaseController.get("/Order/{orderId}/getRelatedObjects")
    def getRelatedObjects(self, orderId: int, embed: Optional[Any] = None, includeItself: Optional[bool] = None, sortByType: Optional[bool] = None) -> list[OrderPosResponse]:
        """Find related objects"""
        return (yield)

    @BaseController.post("/Order/{orderId}/sendViaEmail")
    def sendorderViaEMail(self, orderId: int) -> list[EmailOrder]:
        """Send order via email"""
        return (yield)

    @BaseController.post("/Order/Factory/createPackingListFromOrder")
    def createPackingListFromOrder(self, order_id: int, order_objectName: str, body: CreatePackingListFromOrder) -> OrderResponse:
        """Create packing list from order"""
        return (yield)

    @BaseController.post("/Order/Factory/createContractNoteFromOrder")
    def createContractNoteFromOrder(self, order_id: int, order_objectName: str, body: CreatePackingListFromOrder) -> OrderResponse:
        """Create contract note from order"""
        return (yield)

    @BaseController.get("/Order/{orderId}/getPdf")
    def orderGetPdf(self, orderId: int, download: Optional[bool] = None, preventSendBy: Optional[bool] = None):
        """Retrieve pdf document of an order"""
        return (yield)

    @BaseController.put("/Order/{orderId}/sendBy")
    def orderSendBy(self, orderId: int) -> OrderResponse:
        """Mark order as sent"""
        return (yield)


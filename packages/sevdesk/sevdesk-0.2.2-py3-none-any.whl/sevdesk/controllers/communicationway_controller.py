from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.communicationway import CommunicationWay
from sevdesk.models.communicationwayresponse import CommunicationWayResponse
from sevdesk.models.communicationwayupdate import CommunicationWayUpdate

class CommunicationWayController(BaseController):

    @BaseController.get("/CommunicationWay")
    def getCommunicationWays(self, contact_id: Optional[str] = None, contact_objectName: Optional[str] = None, main: Optional[str] = None, type_: Optional[str] = None) -> list[CommunicationWayResponse]:
        """Retrieve communication ways"""
        return (yield)

    @BaseController.post("/CommunicationWay")
    def createCommunicationWay(self, body: CommunicationWay) -> CommunicationWayResponse:
        """Create a new contact communication way"""
        return (yield)

    @BaseController.get("/CommunicationWay/{communicationWayId}")
    def getCommunicationWayById(self, communicationWayId: int) -> list[CommunicationWayResponse]:
        """Find communication way by ID"""
        return (yield)

    @BaseController.delete("/CommunicationWay/{communicationWayId}")
    def deleteCommunicationWay(self, communicationWayId: int):
        """Deletes a communication way"""
        return (yield)

    @BaseController.put("/CommunicationWay/{communicationWayId}")
    def UpdateCommunicationWay(self, communicationWayId: int, body: CommunicationWayUpdate) -> CommunicationWayResponse:
        """Update a existing communication way"""
        return (yield)

    @BaseController.get("/CommunicationWayKey")
    def getCommunicationWayKeys(self):
        """Retrieve communication way keys"""
        return (yield)


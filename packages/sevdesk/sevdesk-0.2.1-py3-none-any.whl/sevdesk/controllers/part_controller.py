from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.part import Part
from sevdesk.models.partupdate import PartUpdate

class PartController(BaseController):

    @BaseController.get("/Part")
    def getParts(self, name: Optional[str] = None, partNumber: Optional[str] = None) -> list[Part]:
        """Retrieve parts"""
        return (yield)

    @BaseController.post("/Part")
    def createPart(self, body: Part) -> Part:
        """Create a new part"""
        return (yield)

    @BaseController.get("/Part/{partId}")
    def getPartById(self, partId: int) -> list[Part]:
        """Find part by ID"""
        return (yield)

    @BaseController.put("/Part/{partId}")
    def updatePart(self, partId: int, body: PartUpdate) -> Part:
        """Update an existing part"""
        return (yield)

    @BaseController.get("/Part/{partId}/getStock")
    def partGetStock(self, partId: int):
        """Get stock of a part"""
        return (yield)


from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.tagcreateresponse import TagCreateResponse
from sevdesk.models.tagresponse import TagResponse

class TagController(BaseController):

    @BaseController.get("/Tag")
    def getTags(self, id_: Optional[float] = None, name: Optional[str] = None) -> list[TagResponse]:
        """Retrieve tags"""
        return (yield)

    @BaseController.get("/Tag/{tagId}")
    def getTagById(self, tagId: int) -> list[TagResponse]:
        """Find tag by ID"""
        return (yield)

    @BaseController.put("/Tag/{tagId}")
    def updateTag(self, tagId: int) -> TagResponse:
        """Update tag"""
        return (yield)

    @BaseController.delete("/Tag/{tagId}")
    def deleteTag(self, tagId: int):
        """Deletes a tag"""
        return (yield)

    @BaseController.post("/Tag/Factory/create")
    def createTag(self) -> TagCreateResponse:
        """Create a new tag"""
        return (yield)

    @BaseController.get("/TagRelation")
    def getTagRelations(self) -> list[TagCreateResponse]:
        """Retrieve tag relations"""
        return (yield)


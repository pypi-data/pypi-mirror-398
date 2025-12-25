from sevdesk.base.basecontroller import BaseController
from typing import Optional, Any

from sevdesk.undocumented.models.letter import Letter
from sevdesk.undocumented.models.letterresponse import LetterResponse
from sevdesk.undocumented.models.letterupdate import LetterUpdate
from sevdesk.undocumented.models.documentsettings import DocumentSettings

class LetterController(BaseController):

    @BaseController.post("/Letter")
    def createLetter(self, body: Letter) -> LetterResponse:
        """Create a new letter"""
        return (yield)

    @BaseController.get("/Letter")
    def getLetters(self, contact_id: Optional[int] = None, contact_objectName: Optional[str] = None, countAll: Optional[bool] = None, embed: Optional[str] = None, emptyState: Optional[bool] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> list[LetterResponse]:
        """Retrieve letters"""
        return (yield)

    @BaseController.get("/Letter/{letterId}")
    def getLetterById(self, letterId: int) -> LetterResponse:
        """Find letter by ID"""
        return (yield)

    @BaseController.put("/Letter/{letterId}")
    def updateLetter(self, letterId: int, body: LetterUpdate) -> LetterResponse:
        """Update an existing letter"""
        return (yield)

    @BaseController.delete("/Letter/{letterId}")
    def deleteLetter(self, letterId: int):
        """Delete a letter"""
        return (yield)

    @BaseController.post("/Letter/{letterId}/render")
    def letterRender(self, letterId: int, forceReload: Optional[bool] = None, getAsPdf: Optional[bool] = None):
        """Render the pdf document of a letter"""
        return (yield)

    @BaseController.get("/Letter/{letterId}/getLetterJobs")
    def getLetterJobs(self, letterId: int):
        """Get letter rendering jobs"""
        return (yield)

    @BaseController.put("/Letter/{letterId}/changeParameter")
    def changeLetterParameter(self, letterId: int, key: str, value: str, getAsPdf: Optional[bool] = None):
        """Change letter parameter (e.g., logoSize, color)"""
        return (yield)

    @BaseController.put("/Letter/{letterId}/sendBy")
    def letterSendBy(self, letterId: int, sendType: str="VPDF") -> LetterResponse:
        """Mark letter as sent"""
        return (yield)

    @BaseController.get("/Letter/{letterId}/getPdf")
    def letterGetPdf(self, letterId: int, download: Optional[bool] = None, preventSendBy: Optional[bool] = None):
        """Retrieve pdf document of a letter"""
        return (yield)

    @BaseController.get("/SevClient/{sevClientId}/getDocumentSettings")
    def getDocumentSettings(self, sevClientId: int) -> DocumentSettings:
        """Get document settings for PDF generation"""
        return (yield)


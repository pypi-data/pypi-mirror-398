from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.creditnoteposresponse import CreditNotePosResponse

class CreditNotePosController(BaseController):

    @BaseController.get("/CreditNotePos")
    def getcreditNotePositions(self, creditNote_id: Optional[int] = None, creditNote_objectName: Optional[str] = None) -> list[CreditNotePosResponse]:
        """Retrieve creditNote positions"""
        return (yield)


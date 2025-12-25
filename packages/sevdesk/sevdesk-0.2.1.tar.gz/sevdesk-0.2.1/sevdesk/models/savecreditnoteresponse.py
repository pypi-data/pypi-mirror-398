from typing import Optional, Any
from pydantic import BaseModel, Field


class SaveCreditNoteResponse(BaseModel):
    creditNote: Optional[str] = None
    creditNotePos: Optional[Any] = None
    class Config:
        populate_by_name = True
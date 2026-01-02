from typing import Optional, Any
from pydantic import BaseModel, Field


class SaveCreditNote(BaseModel):
    creditNote: str
    creditNotePosSave: Optional[Any] = None
    creditNotePosDelete: Optional[str] = None
    discountSave: Optional[str] = None
    discountDelete: Optional[str] = None
    class Config:
        populate_by_name = True
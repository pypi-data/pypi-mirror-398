from typing import Optional, Any
from pydantic import BaseModel, Field


class SaveInvoiceResponse(BaseModel):
    invoice: Optional[str] = None
    invoicePos: Optional[Any] = None
    filename: Optional[str] = Field(default=None, description="Filename of a previously upload file which should be attached.")
    class Config:
        populate_by_name = True
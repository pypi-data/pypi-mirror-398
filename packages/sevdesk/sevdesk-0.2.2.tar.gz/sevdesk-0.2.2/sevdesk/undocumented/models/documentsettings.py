from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class DocumentSettings(BaseModel):
    """Document Settings für PDF-Generierung"""
    id_: Optional[str] = Field(default=None, alias="id")
    objectName: Optional[str] = None
    additionalInformation: Optional[str] = None
    create: Optional[str] = None
    update: Optional[str] = None
    sevClient: Optional[SevClient] = None
    printCustomerNumber: Optional[bool] = None
    printContactPerson: Optional[bool] = None
    logoSize: Optional[int] = None
    color: Optional[str] = None
    
    class Config:
        populate_by_name = True
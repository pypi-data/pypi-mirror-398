from typing import Optional
from pydantic import BaseModel, Field


class CreditNote_mailResponse(BaseModel):
    id_: Optional[int] = Field(default=None, alias="id")
    objectName: Optional[str] = None
    additionalInformation: Optional[str] = None
    create: Optional[str] = Field(default=None, description="Date of email creation")
    update: Optional[str] = Field(default=None, description="Date of last email update")
    object_: Optional[str] = Field(default=None, alias="object")
    from_: Optional[str] = Field(default=None, alias="from")
    to_: Optional[str] = Field(default=None, alias="to")
    subject: Optional[str] = None
    text: Optional[str] = None
    sevClient: Optional[str] = Field(default=None, description="Client to which creditNote belongs. Will be filled automatically")
    class Config:
        populate_by_name = True
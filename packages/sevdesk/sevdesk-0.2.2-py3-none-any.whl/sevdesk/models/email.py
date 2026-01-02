from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class Email(BaseModel):
    """Email model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The email id")
    objectName: Optional[str] = Field(default=None, description="The email object name")
    create: Optional[str] = Field(default=None, description="Date of mail creation")
    update: Optional[str] = Field(default=None, description="Date of last mail update")
    object_: Optional[str] = Field(default=None, alias="object")
    from_: str = Field(alias="from", description="The sender of the email")
    to_: str = Field(alias="to", description="The recipient of the email")
    subject: str = Field(description="The subject of the email")
    text: Optional[str] = Field(default=None, description="The text of the email")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which mail belongs. Will be filled automatically")
    cc: Optional[str] = Field(default=None, description="A list of mail addresses which are in the cc")
    bcc: Optional[str] = Field(default=None, description="A list of mail addresses which are in the bcc")
    arrived: Optional[str] = Field(default=None, description="Date the mail arrived")
    class Config:
        populate_by_name = True
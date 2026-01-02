from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient

class TagResponse(BaseModel):
    """tag model"""

    id_: Optional[str] = Field(default=None, alias="id", description="Id of the tag")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'Tag'.")
    additionalInformation: Optional[str] = None
    create: Optional[str] = Field(default=None, description="Date of tag creation")
    name: Optional[str] = Field(default=None, description="name of the tag")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice belongs. Will be filled automatically")
    class Config:
        populate_by_name = True
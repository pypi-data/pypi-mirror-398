from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.tag import Tag
from sevdesk.converters.object_ import Object_
from sevdesk.converters.sevclient import SevClient

class TagCreateResponse(BaseModel):
    """tag model"""

    id_: Optional[str] = Field(default=None, alias="id", description="Id of the tag")
    objectName: Optional[str] = Field(default=None, description="Internal object name which is 'TagRelation'.")
    additionalInformation: Optional[str] = None
    create: Optional[str] = Field(default=None, description="Date of tag creation")
    tag: Optional[Tag] = Field(default=None, description="The tag information")
    object_: Optional[Object_] = Field(default=None, alias="object")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice belongs. Will be filled automatically")
    class Config:
        populate_by_name = True
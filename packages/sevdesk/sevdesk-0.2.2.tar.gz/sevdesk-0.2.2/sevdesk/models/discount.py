from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.object_ import Object_

class Discount(BaseModel):
    """Discount model"""

    id_: Optional[str] = Field(default=None, alias="id", description="the id of the discount")
    objectName: Optional[str] = Field(default=None, description="Model name, which is 'Discounts'")
    create: Optional[str] = Field(default=None, description="Date of discount creation")
    update: Optional[str] = Field(default=None, description="Date of last discount update")
    object_: Optional[Object_] = Field(default=None, alias="object", description="The order used for the discount")
    sevClient: Optional[str] = Field(default=None, description="Client to which invoice belongs. Will be filled automatically")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    percentage: Optional[str] = Field(default=None, description="Defines if this is a percentage or an absolute discount")
    value: Optional[str] = Field(default=None, description="Value of the discount")
    isNet: Optional[str] = Field(default=None, description="Defines is the Discount net or gross 0 - gross 1 - net")
    class Config:
        populate_by_name = True
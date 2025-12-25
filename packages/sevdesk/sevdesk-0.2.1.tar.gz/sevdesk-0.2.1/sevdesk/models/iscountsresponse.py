from typing import Optional
from pydantic import BaseModel, Field


class IscountsResponse(BaseModel):
    id_: Optional[int] = Field(default=None, alias="id", description="The id of the discount")
    objectName: Optional[str] = Field(default=None, description="Model name, which is 'Discounts'")
    create: Optional[str] = Field(default=None, description="Date of discount creation")
    update: Optional[str] = Field(default=None, description="Date of last discount update")
    sevClient: Optional[str] = Field(default=None, description="Client to which the discount belongs")
    discount: Optional[str] = Field(default=None, description="Indicates that this is a discount or a surcharge (0 = surcharge, 1 = discount)")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    percentage: Optional[str] = Field(default=None, description="Defines if this is a percentage or an absolute discount")
    value: Optional[str] = Field(default=None, description="Value of the discount")
    isNet: Optional[str] = Field(default=None, description="Defines is the Discount net or gross (0 = net, 1 = gross)")
    class Config:
        populate_by_name = True
from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.creditnote import CreditNote
from sevdesk.converters.part import Part
from sevdesk.converters.unity import Unity
from sevdesk.converters.sevclient import SevClient

class CreditNotePos(BaseModel):
    """creditNote position model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The creditNote position id.")
    objectName: str = Field(description="The creditNote position object name")
    mapAll: bool
    create: Optional[str] = Field(default=None, description="Date of creditNote position creation")
    update: Optional[str] = Field(default=None, description="Date of last creditNote position update")
    creditNote: Optional[CreditNote] = Field(default=None, description="The creditNote to which the position belongs. <span style='color:red'>Required</span> if you want to create/update an credit note position for an existing credit note'")
    part: Optional[Part] = Field(default=None, description="Part from your inventory which is used in the position.")
    quantity: float = Field(description="Quantity of the article/part")
    price: Optional[float] = Field(default=None, description="Price of the article/part. Is either gross or net, depending on the sevdesk account setting.")
    priceNet: Optional[float] = Field(default=None, description="Net price of the part")
    priceTax: Optional[float] = Field(default=None, description="Tax on the price of the part")
    priceGross: Optional[float] = Field(default=None, description="Gross price of the part")
    name: Optional[str] = Field(default=None, description="Name of the article/part.")
    unity: Unity = Field(description="The unit in which the positions part is measured")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which creditNote position belongs. Will be filled automatically")
    positionNumber: Optional[int] = Field(default=None, description="Position number of your position. Can be used to creditNote multiple positions.")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    discount: Optional[float] = Field(default=None, description="An optional discount of the position.")
    optional: Optional[bool] = Field(default=None, description="Defines if the position is optional.")
    taxRate: float = Field(description="Tax rate of the position.")
    sumDiscount: Optional[float] = Field(default=None, description="Discount sum of the position")
    class Config:
        populate_by_name = True
from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.order import Order
from sevdesk.converters.part import Part
from sevdesk.converters.unity import Unity
from sevdesk.converters.sevclient import SevClient

class OrderPos(BaseModel):
    """Order position model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The order position id")
    objectName: Optional[str] = Field(default=None, description="The order position object name")
    create: Optional[str] = Field(default=None, description="Date of order position creation")
    update: Optional[str] = Field(default=None, description="Date of last order position update")
    order: Optional[Order] = Field(default=None, description="The order to which the position belongs.")
    part: Optional[Part] = Field(default=None, description="Part from your inventory which is used in the position.")
    quantity: float = Field(description="Quantity of the article/part")
    price: Optional[float] = Field(default=None, description="Price of the article/part. Is either gross or net, depending on the sevdesk account setting.")
    priceNet: Optional[float] = Field(default=None, description="Net price of the part")
    priceTax: Optional[float] = Field(default=None, description="Tax on the price of the part")
    priceGross: Optional[float] = Field(default=None, description="Gross price of the part")
    name: Optional[str] = Field(default=None, description="Name of the article/part.")
    unity: Unity = Field(description="The unit in which the positions part is measured")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which order position belongs. Will be filled automatically")
    positionNumber: Optional[int] = Field(default=None, description="Position number of your position. Can be used to order multiple positions.")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    discount: Optional[float] = Field(default=None, description="An optional discount of the position.")
    optional: Optional[bool] = Field(default=None, description="Defines if the position is optional.")
    taxRate: float = Field(description="Tax rate of the position.")
    sumDiscount: Optional[float] = Field(default=None, description="Discount sum of the position")
    class Config:
        populate_by_name = True
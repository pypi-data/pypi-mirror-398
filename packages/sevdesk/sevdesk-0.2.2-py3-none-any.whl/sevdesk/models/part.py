from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.category import Category
from sevdesk.converters.unity import Unity
from sevdesk.converters.sevclient import SevClient

class Part(BaseModel):
    """Part model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The part id")
    objectName: Optional[str] = Field(default=None, description="The part object name")
    create: Optional[str] = Field(default=None, description="Date of part creation")
    update: Optional[str] = Field(default=None, description="Date of last part update")
    name: str = Field(description="Name of the part")
    partNumber: str = Field(description="The part number")
    text: Optional[str] = Field(default=None, description="A text describing the part")
    category: Optional[Category] = Field(default=None, description="Category of the part.<br> For all categories, send a GET to /Category?objectType=Part")
    stock: float = Field(description="The stock of the part")
    stockEnabled: Optional[bool] = Field(default=None, description="Defines if the stock should be enabled")
    unity: Unity = Field(description="The unit in which the part is measured")
    price: Optional[float] = Field(default=None, description="Net price for which the part is sold. we will change this parameter so that the gross price is calculated automatically, until then the priceGross parameter must be used.")
    priceNet: Optional[float] = Field(default=None, description="Net price for which the part is sold")
    priceGross: Optional[float] = Field(default=None, description="Gross price for which the part is sold")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which part belongs. Will be filled automatically")
    pricePurchase: Optional[float] = Field(default=None, description="Purchase price of the part")
    taxRate: float = Field(description="Tax rate of the part")
    status: Optional[int] = Field(default=None, description="Status of the part. 50 <-> Inactive - 100 <-> Active")
    internalComment: Optional[str] = Field(default=None, description="An internal comment for the part.<br> Does not appear on invoices and orders.")
    class Config:
        populate_by_name = True
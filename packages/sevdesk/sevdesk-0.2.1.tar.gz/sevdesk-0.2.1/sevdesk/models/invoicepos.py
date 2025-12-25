from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.invoice import Invoice
from sevdesk.converters.part import Part
from sevdesk.converters.unity import Unity
from sevdesk.converters.sevclient import SevClient

class InvoicePos(BaseModel):
    """Invoice position model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The invoice position id. <span style='color:red'>Required</span> if you want to update an invoice position for an existing invoice")
    objectName: str = Field(description="The invoice position object name")
    mapAll: bool
    create: Optional[str] = Field(default=None, description="Date of invoice position creation")
    update: Optional[str] = Field(default=None, description="Date of last invoice position update")
    invoice: Optional[Invoice] = Field(default=None, description="The invoice to which the position belongs.")
    part: Optional[Part] = Field(default=None, description="Part from your inventory which is used in the position.")
    quantity: float = Field(description="Quantity of the article/part")
    price: Optional[float] = Field(default=None, description="Price of the article/part. Is either gross or net, depending on the sevdesk account setting.")
    name: Optional[str] = Field(default=None, description="Name of the article/part.")
    unity: Unity = Field(description="The unit in which the positions part is measured")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice position belongs. Will be filled automatically")
    positionNumber: Optional[int] = Field(default=None, description="Position number of your position. Can be used to order multiple positions.")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    discount: Optional[float] = Field(default=None, description="An optional discount of the position.")
    taxRate: float = Field(description="Tax rate of the position.")
    sumDiscount: Optional[float] = Field(default=None, description="Discount sum of the position")
    sumNetAccounting: Optional[float] = Field(default=None, description="Net accounting sum of the position")
    sumTaxAccounting: Optional[float] = Field(default=None, description="Tax accounting sum of the position")
    sumGrossAccounting: Optional[float] = Field(default=None, description="Gross accounting sum of the position")
    priceNet: Optional[float] = Field(default=None, description="Net price of the part")
    priceGross: Optional[float] = Field(default=None, description="Gross price of the part")
    priceTax: Optional[float] = Field(default=None, description="Tax on the price of the part")
    class Config:
        populate_by_name = True
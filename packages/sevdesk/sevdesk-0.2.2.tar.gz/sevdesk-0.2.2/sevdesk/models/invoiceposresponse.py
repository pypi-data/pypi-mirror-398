from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.invoice import Invoice
from sevdesk.converters.part import Part
from sevdesk.converters.unity import Unity
from sevdesk.converters.sevclient import SevClient

class InvoicePosResponse(BaseModel):
    """Invoice position model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The invoice position id")
    objectName: Optional[str] = Field(default=None, description="The invoice position object name")
    create: Optional[str] = Field(default=None, description="Date of invoice position creation")
    update: Optional[str] = Field(default=None, description="Date of last invoice position update")
    invoice: Optional[Invoice] = Field(default=None, description="The invoice to which the position belongs.")
    part: Optional[Part] = Field(default=None, description="Part from your inventory which is used in the position.")
    quantity: Optional[str] = Field(default=None, description="Quantity of the article/part (fix: API returns string, not boolean)")
    price: Optional[str] = Field(default=None, description="Price of the article/part. Is either gross or net, depending on the sevdesk account setting.")
    name: Optional[str] = Field(default=None, description="Name of the article/part.")
    unity: Optional[Unity] = Field(default=None, description="The unit in which the positions part is measured")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice position belongs. Will be filled automatically")
    positionNumber: Optional[str] = Field(default=None, description="Position number of your position. Can be used to order multiple positions.")
    text: Optional[str] = Field(default=None, description="A text describing your position.")
    discount: Optional[str] = Field(default=None, description="An optional discount of the position.")
    taxRate: Optional[str] = Field(default=None, description="Tax rate of the position.")
    sumDiscount: Optional[str] = Field(default=None, description="Discount sum of the position")
    sumNetAccounting: Optional[str] = Field(default=None, description="Net accounting sum of the position")
    sumTaxAccounting: Optional[str] = Field(default=None, description="Tax accounting sum of the position")
    sumGrossAccounting: Optional[str] = Field(default=None, description="Gross accounting sum of the position")
    priceNet: Optional[str] = Field(default=None, description="Net price of the part")
    priceGross: Optional[str] = Field(default=None, description="Gross price of the part")
    priceTax: Optional[str] = Field(default=None, description="Tax on the price of the part")
    class Config:
        populate_by_name = True
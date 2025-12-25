from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.order import Order

class CreateInvoiceFromOrder(BaseModel):
    """Invoice model"""

    order: Order = Field(description="select the order for which you want to create the invoice")
    type_: Optional[str] = Field(default=None, alias="type", description="defines the type of amount")
    amount: Optional[float] = Field(default=None, description="Amount which has already been paid for this Invoice")
    partialType: Optional[str] = Field(default=None, description="defines the type of the invoice 1. RE - Schlussrechnung 2. TR - Teilrechnung 3. AR - Abschlagsrechnung")
    class Config:
        populate_by_name = True
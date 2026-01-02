from pydantic import BaseModel, Field


class CreatePackingListFromOrder(BaseModel):
    """order model"""

    id_: int = Field(alias="id", description="Unique identifier of the order")
    objectName: str = Field(description="Model name, which is 'Order'")
    class Config:
        populate_by_name = True
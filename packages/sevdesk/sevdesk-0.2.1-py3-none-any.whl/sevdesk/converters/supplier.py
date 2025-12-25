from pydantic import BaseModel, Field

class Supplier(BaseModel):
    id_: int = Field(alias="id")
    objectName: str
    class Config:
        populate_by_name = True
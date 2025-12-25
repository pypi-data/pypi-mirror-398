from pydantic import BaseModel, Field

class AddressCountry(BaseModel):
    id_: int = Field(alias="id")
    objectName: str
    class Config:
        populate_by_name = True
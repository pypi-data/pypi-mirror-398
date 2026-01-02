from pydantic import BaseModel, Field

class AccountingType(BaseModel):
    id_: str = Field(alias="id")
    objectName: str
    class Config:
        populate_by_name = True
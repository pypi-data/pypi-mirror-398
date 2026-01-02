from pydantic import BaseModel, Field

class CreditNote(BaseModel):
    id_: str = Field(alias="id")
    objectName: str
    class Config:
        populate_by_name = True
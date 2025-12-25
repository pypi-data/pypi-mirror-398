from pydantic import BaseModel, Field

class Unity(BaseModel):
    id_: int = Field(alias="id")
    objectName: str
    class Config:
        populate_by_name = True
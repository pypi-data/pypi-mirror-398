from pydantic import BaseModel, Field


class ChangeLayout(BaseModel):
    """Layout model"""

    key: str = Field(description="the type to be changed")
    value: str = Field(description="the id/value of the template/letterpaper/language/payPal.")
    class Config:
        populate_by_name = True
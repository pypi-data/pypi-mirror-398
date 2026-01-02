from typing import Optional, Any
from pydantic import BaseModel, Field


class ReceiptGuideDto(BaseModel):
    """Model holds data about a single selectable account with additional information matching to that account."""

    accountDatevId: Optional[int] = Field(default=None, description="The ID of the matching account datev")
    accountNumber: Optional[str] = Field(default=None, description="The account number of the account datev (dependent on the active accounting system of the client)")
    accountName: Optional[str] = Field(default=None, description="The name of the account")
    description: Optional[str] = Field(default=None, description="The description of the account and/or what the account is used for")
    allowedTaxRules: Optional[Any] = Field(default=None, description="An array that holds all possible tax rules for this account")
    allowedReceiptTypes: Optional[Any] = Field(default=None, description="An array that holds the viable receipt types for this account")
    class Config:
        populate_by_name = True
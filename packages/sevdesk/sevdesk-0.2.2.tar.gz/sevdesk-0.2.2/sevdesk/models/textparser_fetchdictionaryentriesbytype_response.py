from typing import Optional, Any
from pydantic import BaseModel, Field


class Textparser_fetchDictionaryEntriesByType_response(BaseModel):
    """Textparser fetchDictionaryEntriesByType model"""

    key: Optional[str] = None
    value: Optional[Any] = None
    class Config:
        populate_by_name = True
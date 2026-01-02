from typing import Optional
from pydantic import BaseModel

class Object(BaseModel):
    id: int
    objectName: str

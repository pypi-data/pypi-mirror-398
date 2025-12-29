from typing import Optional

from pydantic import BaseModel, Field


class Awards(BaseModel):
    id: int = Field(gt=0)
    name: str
    coins: int = Field(ge=0)
    image: Optional[str] = Field(default=None)

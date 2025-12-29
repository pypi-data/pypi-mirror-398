from typing import Optional

from pydantic import BaseModel, Field


class Allergens(BaseModel):
    id: int = Field(gt=0)
    name: str
    image: Optional[str] = Field(default=None)

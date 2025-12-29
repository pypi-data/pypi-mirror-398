from typing import Optional

from pydantic import BaseModel, Field


class OptionsModifiers(BaseModel):
    id: int = Field(gt=0)
    name: str
    is_quantifiable: bool = Field(default=False)
    image: Optional[str] = Field(default=None)
    min_value: int = Field(default=0, ge=0)
    max_value: int = Field(default=0, ge=0)
    order: Optional[int] = Field(default=None, ge=0)

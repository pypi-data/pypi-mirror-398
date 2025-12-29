from typing import Optional

from pydantic import BaseModel, Field


class Screens(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(...)
    categories: Optional[list[int]] = Field(default=None)
    modifiers: Optional[list[int]] = Field(default=None)
    tpv: list[int]
    show_various: bool = Field(default=True)

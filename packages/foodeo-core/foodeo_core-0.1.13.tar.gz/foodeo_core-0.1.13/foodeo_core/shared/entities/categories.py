from typing import Optional

from pydantic import BaseModel, Field


class Categories(BaseModel):
    id: int = Field(gt=0)
    name: str
    app_text: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    is_subcategory: bool = Field(default=False)
    customer_active: bool = Field(default=True)
    is_active: bool = Field(default=True)
    is_available: bool = Field(default=False)
    order: Optional[int] = Field(default=None)


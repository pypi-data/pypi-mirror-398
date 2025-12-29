from typing import Optional

from pydantic import BaseModel, Field


class Clients(BaseModel):
    id: int = Field(gt=0)
    first_name: str
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    dni_cif: Optional[str] = Field(default=None)
    by_default: bool = Field(default=False)
    communications: bool = Field(default=False)
    digital_card_user: Optional[int] = Field(default=None, gt=0)

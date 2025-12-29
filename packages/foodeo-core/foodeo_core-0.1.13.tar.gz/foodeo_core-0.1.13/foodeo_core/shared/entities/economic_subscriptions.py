from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class EconomicSubscriptions(BaseModel):
    id: int = Field(gt=0)
    serial: str = Field(...)
    amount: Decimal = Field(default=Decimal(0))
    description: Optional[str]
    user: int
    credit_card: bool = Field(default=False)

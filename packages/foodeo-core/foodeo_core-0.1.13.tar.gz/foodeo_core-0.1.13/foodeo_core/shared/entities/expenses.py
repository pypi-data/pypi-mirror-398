from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import PAYED_WITH_ENUM, ExpensesStatusEnum


class Expenses(BaseModel):
    id: int = Field(gt=0)
    serial: str = Field(...)
    user: int
    importe: Decimal = Field(default=Decimal(0))
    payed_with: PAYED_WITH_ENUM = Field(default=PAYED_WITH_ENUM.credit_card)
    description: Optional[str]
    status: ExpensesStatusEnum = Field(default=ExpensesStatusEnum.created)

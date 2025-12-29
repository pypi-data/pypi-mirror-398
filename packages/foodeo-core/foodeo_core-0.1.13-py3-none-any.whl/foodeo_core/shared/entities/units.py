from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import UnitEnum


class Units(BaseModel):
    id: int = Field(gt=0)
    name: str
    type: UnitEnum = Field(default=UnitEnum.quantity)
    basic: bool = Field(default=True)
    value: Optional[Decimal] = Field(default=None, gt=0)
    value_conversion: Optional[Decimal] = Field(default=None, gt=0)
    unit_reference: Optional[int] = Field(default=None)

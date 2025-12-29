from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import UnitOfMeasureEnum


class Norm(BaseModel):
    unit_of_measure: Optional[UnitOfMeasureEnum] = Field(default=UnitOfMeasureEnum.ud)
    value: Optional[Decimal] = Field(default=Decimal(1), gt=0)

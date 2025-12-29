from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Ingredients(BaseModel):
    id: int = Field(gt=0)
    serial: Optional[str] = None
    name: str
    image: Optional[str] = Field(default=None)
    price: Decimal = Decimal(0)
    stk_uuid: Optional[UUID] = None
    description: Optional[str] = None
    unit: int
    min_stock: Decimal = Decimal(0)
    final_qty_min_stock: Decimal = Decimal(0)
    old_price: Optional[Decimal]
    iva: Optional[Decimal] = None
    sku: Optional[str] = None
    is_active: bool

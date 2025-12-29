from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseProducts(BaseModel):
    id: int = Field(gt=0)
    serial: Optional[str] = None
    name: str
    category: int = Field(...)
    category_name: str
    image: Optional[str] = Field(default=None)
    price: Decimal = Decimal(0)
    qty: Optional[int] = None
    description: Optional[str] = None
    is_offer: bool = False
    date_at: Optional[date] = None
    stk_uuid: Optional[UUID] = None
    unit_value: Decimal = Decimal(1)
    unit: int
    min_stock: Decimal = Decimal(0)
    final_qty_min_stock: Decimal = Decimal(0)
    order_number: Optional[int] = None
    order: Optional[int] = None
    purchase_price: Decimal = Decimal(0)
    qty_existence: Optional[int] = None
    iva: Optional[Decimal] = None

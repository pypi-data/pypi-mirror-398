from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import DiscountPromotionEnum


class Promotions(BaseModel):
    id: int = Field(gt=0)
    name: str
    qr: str
    code: str
    price: Decimal = Field(default=Decimal(0), ge=0)
    discount_type: DiscountPromotionEnum
    start_date: datetime
    end_date: datetime
    limit_uses: int = Field(default=0)
    limit_uses_client: int = Field(default=0)
    description: Optional[str] = Field(default=None)
    total_uses: int = Field(default=0)

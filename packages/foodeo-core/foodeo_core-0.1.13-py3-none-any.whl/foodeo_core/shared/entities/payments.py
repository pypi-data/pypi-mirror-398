from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from foodeo_core.shared.enums import CommandEnum, RequestEnum, PaymentType, FromClient, PaymentStatus, PAYED_WITH_ENUM


class Payments(BaseModel):
    id: Optional[int] = Field(None)
    serial: Optional[str] = Field(None)
    type: RequestEnum = Field(...)
    request_type: CommandEnum = Field(...)
    payment_type: PaymentType = Field(...)
    from_client: FromClient = Field(...)
    status: PaymentStatus = Field(...)
    domicile_price: Optional[Decimal] = Field(...)
    importe: Optional[Decimal] = Field(...)
    tip: Optional[Decimal] = Field(...)
    payed_with: PAYED_WITH_ENUM = Field(...)

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt

from foodeo_core.shared.enums import RequestEnum, StatusEnum, FromClientEnum, TipOptionsEnum
from .irequests import IRequests
from .requests_items import ProductInRequest


class Request(IRequests):
    type: RequestEnum = Field(...)
    from_client: FromClientEnum = Field(...)
    products: list[ProductInRequest] = Field(..., min_length=1)
    tip_option: TipOptionsEnum = Field(default=TipOptionsEnum.no_tip)
    tip_amount: Optional[Decimal] = Field(ge=0, default=Decimal(0))
    status: Optional[StatusEnum] = Field(None)
    worker: Optional[int] = Field(None)
    command_id: Optional[int] = Field(None)
    user_id: Optional[int] = None
    tpv_key: Optional[str] = ""
    employee: Optional[int] = None
    request_price: Optional[Decimal] = None


class LocalRequest(Request):
    tenant: str = Field(min_length=1, default="DEFAULT")
    qr: str = Field(..., min_length=1)
    command_guests: Optional[PositiveInt] = None


class CloseWith(BaseModel):
    dataphone: Optional[int] = None
    cashier: Optional[int] = None
    platform: Optional[str] = None


class BarraRequestCloseWithConfig(BaseModel):
    close_with: Optional[CloseWith] = None


class BarraRequest(Request):
    config: Optional[BarraRequestCloseWithConfig] = None
    tip_amount: Decimal = Field(default=Decimal(0), ge=0)
    tip_option: TipOptionsEnum = TipOptionsEnum.no_tip


class KioskoRequest(Request):
    tip_amount: Decimal = Field(default=Decimal(0), ge=0)
    tip_option: TipOptionsEnum = TipOptionsEnum.no_tip


class PickupRequest(Request):
    shift_time: str = Field(...)
    soon_as_possible: bool = Field(default=False)
    delivery_date: date = Field(default=datetime.today().date())


class DomicileRequest(Request):
    address: Optional[int] = Field(None)
    dealer: Optional[int] = Field(None)
    shift_time: str = Field(...)
    soon_as_possible: bool = Field(default=False)
    delivery_date: date = Field(default=datetime.today().date())

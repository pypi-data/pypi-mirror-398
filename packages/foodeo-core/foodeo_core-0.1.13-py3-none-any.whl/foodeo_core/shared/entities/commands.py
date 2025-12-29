from decimal import Decimal
from typing import Optional

from pydantic import Field, conint, BaseModel

from foodeo_core.shared.enums import CommandEnum, CommandStatusEnum, TipOptionsEnum
from . import ProductInCommand
from .irequests import IRequests


class Command(IRequests):
    type: CommandEnum = Field(...)
    products: list[ProductInCommand] = Field(..., min_length=1)
    tip_option: TipOptionsEnum = TipOptionsEnum.no_tip
    tip_amount: Optional[Decimal] = Field(ge=0, default=Decimal(0))
    status: Optional[CommandStatusEnum] = Field(None)
    price: Optional[Decimal] = Field(ge=0, default=Decimal(0))
    original_price: Optional[Decimal] = Field(ge=0, default=Decimal(0))


class LocalCommand(Command):
    tenant: str = Field(min_length=1, default="DEFAULT")
    table: int = Field(...)
    qr: str = Field(...)
    command_guests: Optional[conint(ge=0)] = None


class BarraCommand(Command):
    pass


class KioskoCommand(Command):
    pass


class PickupCommand(Command):
    client: int = Field(..., gt=0)


class DomicileCommand(Command):
    client: int = Field(..., gt=0)


class TipCalculation(BaseModel):
    price: Decimal
    type: str
    domicile_price: Optional[Decimal] = None
    tip_option: TipOptionsEnum = TipOptionsEnum.no_tip
    tip_amount: Decimal = Field(ge=0, default=Decimal(0))

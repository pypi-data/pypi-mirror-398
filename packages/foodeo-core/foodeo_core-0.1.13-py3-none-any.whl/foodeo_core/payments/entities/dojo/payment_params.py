from pydantic import BaseModel
from decimal import Decimal


class DojoPaymentParams(BaseModel):
    command_id: int
    command_price: Decimal
    command_tip: Decimal
    dataphone_key: str
    currency: str


class DojoCancelParams(BaseModel):
    command_id: int
    dataphone_key: str

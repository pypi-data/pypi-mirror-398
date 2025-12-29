from decimal import Decimal

from pydantic import BaseModel


class CashmaticPaymentExtraParams(BaseModel):
    tpv_key: str
    local_id: int
    user_id: int
    user_token: str
    web_client: str


class CashmaticCancelExtraParams(BaseModel):
    tpv_key: str
    local_id: int
    user_id: int


class CashmaticPaymentParams(CashmaticPaymentExtraParams):
    username: str
    password: str
    ip_address: str
    port: str
    timeout: int
    command_id: int
    command_price: Decimal
    command_serial: str


class CashmaticCancelParams(CashmaticCancelExtraParams):
    username: str
    password: str
    ip_address: str
    port: str
    timeout: int
    command_id: int
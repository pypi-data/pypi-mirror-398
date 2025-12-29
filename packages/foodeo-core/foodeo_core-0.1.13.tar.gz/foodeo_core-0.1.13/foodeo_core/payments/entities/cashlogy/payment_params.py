from decimal import Decimal

from pydantic import BaseModel


class CashlogyPaymentExtraParams(BaseModel):
    tpv_key: str
    local_id: int
    user_id: int
    user_token: str
    web_client: str


class CashlogyPaymentParams(CashlogyPaymentExtraParams):
    ip_address: str
    port: str
    timeout: int
    command_id: int
    command_price: Decimal
    cashier_number: int

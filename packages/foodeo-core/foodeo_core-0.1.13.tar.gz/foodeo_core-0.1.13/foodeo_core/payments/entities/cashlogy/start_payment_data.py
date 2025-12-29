from pydantic import BaseModel


class CashlogyPaymentExtraData(BaseModel):
    tpv: str
    local_id: int
    command_id: int
    user_id: int
    user_token: str
    web_client: str


class CashlogyPaymentMainData(BaseModel):
    timeout: int
    cashier_number: int
    amount: int
    reason: str
    reference: int
    extras: CashlogyPaymentExtraData


class ConfigCashlogyPaymentData(BaseModel):
    url: str
    data: CashlogyPaymentMainData


class CashlogyPaymentData(BaseModel):
    model: int
    cashlogy_data: ConfigCashlogyPaymentData

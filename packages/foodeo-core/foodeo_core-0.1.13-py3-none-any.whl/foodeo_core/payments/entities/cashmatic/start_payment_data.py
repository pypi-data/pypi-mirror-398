from pydantic import BaseModel, Field


class CashmaticPaymentExtraData(BaseModel):
    tpv: str
    local_id: int
    command_id: int
    user_id: int
    user_token: str
    web_client: str


class CashmaticPaymentMainData(BaseModel):
    timeout: int
    amount: int
    reason: str
    reference: str
    queueAllowed: bool = Field(default=False)
    extras: CashmaticPaymentExtraData


class ConfigCashmaticPaymentData(BaseModel):
    operation: int
    username: str
    password: str
    url: str
    data: CashmaticPaymentMainData


class CashmaticPaymentData(BaseModel):
    model: int
    cashmatic_data: ConfigCashmaticPaymentData

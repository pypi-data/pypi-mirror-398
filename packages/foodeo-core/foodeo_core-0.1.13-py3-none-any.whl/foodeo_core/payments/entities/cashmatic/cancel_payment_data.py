from pydantic import BaseModel


class CashmaticCancelExtraData(BaseModel):
    tpv: str
    local_id: int
    command_id: int
    user_id: int


class CashmaticCancelMainData(BaseModel):
    timeout: int
    extras: CashmaticCancelExtraData


class ConfigCashmaticCancelData(BaseModel):
    operation: int
    username: str
    password: str
    url: str
    data: CashmaticCancelMainData


class CashmaticCancelData(BaseModel):
    model: int
    cashmatic_data: ConfigCashmaticCancelData

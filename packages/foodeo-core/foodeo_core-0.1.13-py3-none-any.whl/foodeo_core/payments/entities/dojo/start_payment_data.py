from pydantic import BaseModel


class PaymentDojoParams(BaseModel):
    tid: str
    currency: str
    amount: int


class PaymentDojoData(BaseModel):
    jsonrpc: str
    method: str
    id: int
    params: PaymentDojoParams

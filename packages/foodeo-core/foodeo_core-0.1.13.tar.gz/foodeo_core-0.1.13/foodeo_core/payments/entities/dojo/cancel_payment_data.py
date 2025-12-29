from pydantic import BaseModel


class CancelDojoParams(BaseModel):
    tid: str


class CancelDojoData(BaseModel):
    jsonrpc: str
    method: str
    id: int
    params: CancelDojoParams

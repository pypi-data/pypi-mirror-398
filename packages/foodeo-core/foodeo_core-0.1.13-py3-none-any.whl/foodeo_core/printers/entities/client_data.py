from pydantic import BaseModel, ConfigDict
from typing import Optional


class ClientData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_name: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None



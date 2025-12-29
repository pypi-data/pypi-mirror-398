from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClientAddressData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_name: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None

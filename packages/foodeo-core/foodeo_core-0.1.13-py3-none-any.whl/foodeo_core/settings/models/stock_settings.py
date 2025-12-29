from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StockSettings(BaseModel):
    stock: Optional[UUID]

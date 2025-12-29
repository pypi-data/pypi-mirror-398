from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import FromClientEnum, ReservationsStatusEnum


class Reservations(BaseModel):
    id: int = Field(gt=0)
    date: date
    client: int
    qty_person: int
    status: ReservationsStatusEnum = Field(default=ReservationsStatusEnum.NEW)
    from_client: FromClientEnum = Field(default=FromClientEnum.web)
    observations: Optional[str] = Field(default=None)

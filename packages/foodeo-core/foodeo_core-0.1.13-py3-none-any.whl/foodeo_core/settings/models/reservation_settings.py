from typing import Optional, Annotated

from pydantic import BaseModel, Field


class ReservationSettings(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    min_clients: int
    max_clients: int
    mean_duration: Annotated[int, Field(ge=0)]
    interval: Annotated[int, Field(ge=0)]

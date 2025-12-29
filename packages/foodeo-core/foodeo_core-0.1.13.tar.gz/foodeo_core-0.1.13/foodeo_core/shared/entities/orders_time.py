from pydantic import BaseModel, Field


class OrdersTime(BaseModel):
    id: int = Field(gt=0)
    time_in_minutes: int = Field(default=15, ge=0)

from typing import Optional

from pydantic import BaseModel, Field


class Addresses(BaseModel):
    id: int = Field(gt=0)
    client: int
    street: str
    postal_code: Optional[str] = Field(default=None)
    city: str
    state: str
    reference: Optional[str] = Field(default=None)
    street_number: Optional[str] = Field(default=None)
    floor_and_door: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)

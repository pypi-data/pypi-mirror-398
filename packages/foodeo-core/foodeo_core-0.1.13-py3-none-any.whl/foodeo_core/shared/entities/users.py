from typing import Optional

from pydantic import BaseModel, Field


class Users(BaseModel):
    id: int = Field(gt=0)
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    address: Optional[str]
    role_id: int
    role: str
    phone: Optional[str]
    is_active: bool
    point: int = Field(default=0)
    coins: int = Field(default=0)
    level: str = Field(default="bronze")
    communications: bool

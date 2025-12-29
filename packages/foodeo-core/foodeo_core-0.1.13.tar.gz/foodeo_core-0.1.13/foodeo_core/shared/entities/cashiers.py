from pydantic import BaseModel, Field


class Cashiers(BaseModel):
    id: int = Field(gt=0)
    name: str
    printer: int
    pulse: int = Field(default=200, ge=0)
    port: int = Field(default=0, ge=0)

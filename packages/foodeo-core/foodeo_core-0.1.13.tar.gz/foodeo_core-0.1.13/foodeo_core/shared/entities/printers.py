from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import PRINTER_WIDTH_OPTIONS


class Printer(BaseModel):
    created_at: datetime
    updated_at: datetime
    id: Optional[int] = Field(None)
    name: str
    zone: Optional[list[int]] = Field(default=[])
    tpv: Optional[list[int]] = Field(default=[])
    allow_to_march: Optional[bool] = Field(default=False)
    printer_width: Optional[PRINTER_WIDTH_OPTIONS] = Field(...)

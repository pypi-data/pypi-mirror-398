from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.enums import DaysChoicesEnum


class BarsHours(BaseModel):
    id: int = Field(gt=0)
    day: DaysChoicesEnum
    closed: bool
    open_time: Optional[str]
    close_time: Optional[str]

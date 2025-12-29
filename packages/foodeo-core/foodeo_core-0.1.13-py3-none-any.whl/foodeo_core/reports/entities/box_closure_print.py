from pydantic import BaseModel, Field, PositiveInt

from foodeo_core.reports.entities import BoxClosure


class BoxClosurePrint(BaseModel):
    cashier_close_data: BoxClosure = Field(..., alias='cashierCloseData')
    printer: str = Field(..., min_length=1, max_length=250)
    printer_qty: PositiveInt = Field(...)
    printer_width: str = Field(..., min_length=1, max_length=250)
    model: PositiveInt = Field(...)

    class ConfigDict:
        populate_by_name = True

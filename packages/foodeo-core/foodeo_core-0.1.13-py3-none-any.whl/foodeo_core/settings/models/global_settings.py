from decimal import Decimal
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class GlobalSettings(BaseModel):
    currency: str
    language: str
    language_web_menu: str
    logo: Optional[str]
    use_cashmatic: bool
    use_modifiers: bool = True
    use_payment_terminal: bool
    use_touch_keyboard: bool
    close_barra_order_auto: bool
    close_local_order_auto: bool
    select_employee_before_order: bool
    show_category_name: bool
    new_request_sound: bool
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    iva: Decimal
    min_stock: int
    timezone: ZoneInfo
    street: Optional[str]
    postal_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    reference: Optional[str]
    street_number: Optional[str]
    floor_and_door: Optional[str]
    place_id: Optional[UUID]
    use_fiskaly: bool
    use_cashlogy: bool

    class Config:
        arbitrary_types_allowed = True

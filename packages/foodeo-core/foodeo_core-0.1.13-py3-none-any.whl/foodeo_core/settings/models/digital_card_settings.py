from typing import Optional

from pydantic import BaseModel, Field


class DigitalCardSettings(BaseModel):
    logo: Optional[str]
    header_image: Optional[str]
    kiosko_image: Optional[str]
    title: Optional[str]
    subtitle: Optional[str]
    description: Optional[str]
    principal_color: str = Field(default="#EFA81B")
    page_background_color: str = Field(default="#FFFFFF")
    header_background_color: str = Field(default="#F7F7F7")
    minimal_order_domicile: int = Field(default=1)
    allow_tips: bool = Field(default=False)
    email: Optional[str]
    call_waiter: bool = Field(default=False)
    bookings: bool = Field(default=False)
    local_orders: bool = Field(default=False)
    use_awards: bool = Field(default=False)
    enable_promotion: bool = Field(default=False)
    message_order_cash_accepted_kiosko: Optional[str]
    message_order_card_accepted_kiosko: Optional[str]
    message_order_accepted: Optional[str]

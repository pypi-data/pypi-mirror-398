from pydantic import BaseModel


class TicketStyleSettings(BaseModel):
    name: str
    size: int
    style: str


class KitchenTicketSettings(BaseModel):
    show_local_header: bool
    show_domicile_header: bool
    show_price_per_unit: bool
    show_total_price: bool
    group_by_orders: bool
    show_person_name: bool
    show_command_guests: bool
    header_font: TicketStyleSettings
    details_font: TicketStyleSettings
    print_by: str

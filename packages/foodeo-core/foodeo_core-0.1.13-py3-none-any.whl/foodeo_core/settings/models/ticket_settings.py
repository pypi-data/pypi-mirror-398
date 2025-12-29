from typing import Optional

from pydantic import BaseModel


class TicketSettings(BaseModel):
    heading: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    nif_cif: Optional[str]
    reason: Optional[str]
    use_printer: bool
    qty_client_ticket: int
    qty_kitchen_ticket: int
    order_by: str
    ticket_kitchen_domicile_or_pickup: bool
    ticket_kitchen_local: bool
    ticket_kitchen_barra: bool
    ticket_client_domicile_or_pickup: bool
    ticket_client_local: bool
    ticket_client_barra: bool
    ticket_text: str
    ticket_close_command: bool

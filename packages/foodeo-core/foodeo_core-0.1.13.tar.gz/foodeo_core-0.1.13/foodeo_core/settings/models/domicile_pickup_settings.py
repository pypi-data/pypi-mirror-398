from decimal import Decimal
from typing import Optional, List, Annotated

from pydantic import BaseModel
import annotated_types

NonNegativeInt = Annotated[int, annotated_types.Ge(0)]


class DomicilePickupSettings(BaseModel):
    price_domicile_service: Decimal
    block_domicile_order: bool
    block_pickup_order: bool
    minimal_amount_domicile: Decimal
    auto_accept_domicile: bool
    auto_accept_pickup: bool
    allow_order_time_delay: bool
    shift_duration: NonNegativeInt
    minimal_anticipation_pickup: NonNegativeInt
    minimal_anticipation_domicile: NonNegativeInt
    max_products_by_turn: Optional[NonNegativeInt]
    categories_ids: List[int]
    maximum_radius_domicile: Decimal
    domicile_orders_limit: Optional[NonNegativeInt]
    request_without_client_domicile: bool
    request_without_client_pickup: bool

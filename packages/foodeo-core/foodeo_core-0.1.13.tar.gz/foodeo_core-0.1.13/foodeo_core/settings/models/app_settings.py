from typing import Optional

from pydantic import BaseModel

from foodeo_core.shared.enums import PAYMENTS_SHAPE


class AppSettings(BaseModel):
    text_local: Optional[str]
    local_payments: PAYMENTS_SHAPE
    domicile_payments: PAYMENTS_SHAPE
    pickup_payments: PAYMENTS_SHAPE
    use_vibrant: bool

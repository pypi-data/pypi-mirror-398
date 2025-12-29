from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, condecimal, Field, model_validator, field_serializer

from foodeo_core.reports.entities import IVAData

MonetaryField = condecimal(max_digits=10, decimal_places=2)


class CLOSE_TYPE(str, Enum):
    CLOSE_BOX = 'close_box'
    CLOSE_SHIFT = 'close_shift'


class BoxClosure(BaseModel):
    # Header of close box (OK)

    id: int = Field(...)
    close_type: CLOSE_TYPE = Field(...)
    social_reason: str
    nif_cif: str
    user: str = Field(...)
    serial: str = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    # Accounting attributes of box closure (OK)

    base_imp: Optional[MonetaryField] = None
    cash_register: Optional[MonetaryField] = None
    initial_import: Optional[MonetaryField] = None
    iva: Optional[MonetaryField] = None

    unbalance: Optional[MonetaryField] = None
    card_bank: Optional[MonetaryField] = None
    card_unbalance: Optional[MonetaryField] = None

    # By type of order (OK)

    total_barra: Optional[MonetaryField] = None
    total_barra_credit_card: Optional[MonetaryField] = None
    total_general_barra: Optional[MonetaryField] = None

    total_domicilio: Optional[MonetaryField] = None
    total_domicilio_credit_card: Optional[MonetaryField] = None
    total_general_domicilio: Optional[MonetaryField] = None

    total_economic_subscription: Optional[MonetaryField] = None
    total_expenses_cash: Optional[MonetaryField] = None
    total_expenses_credit_card: Optional[MonetaryField] = None

    total_local: Optional[MonetaryField] = None
    total_local_credit_card: Optional[MonetaryField] = None
    total_general_local: Optional[MonetaryField] = None

    total_recoger: Optional[MonetaryField] = None
    total_recoger_credit_card: Optional[MonetaryField] = None
    total_general_recoger: Optional[MonetaryField] = None

    total_general: Optional[MonetaryField] = None
    total_general_expenses: Optional[MonetaryField] = None
    total_general_tips: Optional[MonetaryField] = None
    total_general_sales: Optional[MonetaryField] = None

    total_imp: Optional[MonetaryField] = None
    total_cash_box: Optional[MonetaryField] = None
    total_cash: Optional[MonetaryField] = None
    total_credit_card: Optional[MonetaryField] = None
    total_discounted: Optional[MonetaryField] = None

    # Other fields (OK)

    iva_data: Optional[IVAData] = Field(default=None, alias='ivaData')

    # Model validators (OK)

    @model_validator(mode="after")
    def build_iva_data(self):
        self.iva_data = IVAData(iva=self.iva, total_imp=self.total_imp, base_imp=self.base_imp)
        return self

    @field_serializer("created_at", "updated_at")
    def datetime_serializer(self, date_time: datetime) -> str:
        return date_time.isoformat()

    @field_serializer("base_imp", "cash_register", "initial_import", "iva", "unbalance", "card_bank", "card_unbalance",
                      "total_barra", "total_barra_credit_card", "total_general_barra", "total_domicilio",
                      "total_domicilio_credit_card", "total_general_domicilio", "total_economic_subscription",
                      "total_expenses_cash", "total_expenses_credit_card", "total_local", "total_local_credit_card",
                      "total_general_local", "total_recoger", "total_recoger_credit_card", "total_general_recoger",
                      "total_general", "total_general_expenses", "total_general_tips", "total_general_sales",
                      "total_imp", "total_cash_box", "total_cash", "total_credit_card", "total_discounted")
    def monetary_field_serializer(self, value: Decimal) -> float:
        return float(value)

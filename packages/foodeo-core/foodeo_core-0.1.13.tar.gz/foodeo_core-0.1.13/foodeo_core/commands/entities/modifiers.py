from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TIPS_OPTIONS(str, Enum):
    FIVE_PERCENT = '5%'
    TEN_PERCENT = '10%'
    OTHER = 'other'
    NO_TIP = 'no_tip'


class COMMANDS_TYPES(str, Enum):
    DOMICILE = 'domicile'
    RECOGER = 'recoger'
    LOCAL = 'local'
    BARRA = 'barra'
    KIOSKO = "kiosko"


class ModifierData(BaseModel):
    modifier_id: int
    modifier_name: str
    modifier_image: Optional[str] = None
    max_value: int
    min_value: int


class OptionData(BaseModel):
    option_id: int
    option_name: str
    option_image: Optional[str] = None
    max_value: int
    min_value: int
    qty: int = 0
    price: Decimal = Field(default=Decimal(0))
    importe: Decimal = Field(default=Decimal(0))


class ModifierChildData(BaseModel):
    modifier_child_name: Optional[str] = None
    modifier_child_image: Optional[str] = None
    modifier_child_id: int
    max_value_modifier_child: int
    min_value_modifier_child: int


class OptionChildData(BaseModel):
    option_child_id: Optional[int] = None
    option_child_name: Optional[str] = None
    option_child_image: Optional[str] = None
    max_value_option_child: int
    min_value_option_child: int
    qty_child: int = 0
    price_child: Decimal = Field(default=Decimal(0))
    importe_child: Decimal = Field(default=Decimal(0))


class ModifierRequestData(BaseModel):
    request_field: str
    request_modifier_id: Optional[int] = None

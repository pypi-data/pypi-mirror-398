from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, ConfigDict, NonNegativeInt

from foodeo_core.shared.enums import UnitOfMeasureEnum
from .discounts import Discount
from .norms import Norm


class PRODUCT_TYPE_NAME(str, Enum):
    REQUEST_TABLE = "request_table"
    REQUEST_ITEM = "request_item"


class REQUEST_KIND(str, Enum):
    NORMAL = "normal"
    CORRECTIONS = "corrections"


class IOptionChildRequest(ABC, BaseModel):
    id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)


class IModifierChildRequest(ABC, BaseModel):
    id: int = Field(..., gt=0)
    modifier_id_field: Optional[int] = None
    options: list[IOptionChildRequest] = []


class IOptionRequest(ABC, BaseModel):
    id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    modifiers: Optional[list[IModifierChildRequest]] = []


class IModifierRequest(ABC, BaseModel):
    id: Optional[int] = None
    options: list[IOptionRequest] = []
    modifiers_id: Optional[int] = None
    modifiers_name: Optional[str] = None
    modifiers_image: Optional[str] = None
    max_value_modifiers: Optional[int] = 0
    min_value_modifiers: Optional[int] = 0
    options_id: Optional[int] = None
    options_name: Optional[str] = None
    options_image: Optional[str] = None
    max_value_options: Optional[int] = 0
    min_value_options: Optional[int] = 0
    qty: Optional[int] = None
    price: Optional[Decimal] = Decimal(0)
    importe: Optional[Decimal] = Decimal(0)
    modifiers_child_id: Optional[int] = None
    modifiers_child_name: Optional[str] = None
    modifiers_child_image: Optional[str] = None
    max_value_modifiers_child: Optional[int] = 0
    min_value_modifiers_child: Optional[int] = 0
    options_child_id: Optional[int] = None
    options_child_name: Optional[str] = None
    options_child_image: Optional[str] = None
    max_value_options_child: Optional[int] = 0
    min_value_options_child: Optional[int] = 0
    qty_child: Optional[int] = None
    price_child: Optional[Decimal] = Decimal(0)
    importe_child: Optional[Decimal] = Decimal(0)
    modifier_id_field: Optional[int] = None


class ModifiersRequest(IModifierRequest):
    pass


class IProductsRequest(ABC, BaseModel):
    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)
    name: str = Field(...)
    qty: NonNegativeInt = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    is_discounted: Optional[bool] = Field(None)
    unit_name: Optional[UnitOfMeasureEnum] = Field(default=UnitOfMeasureEnum.ud)
    unit_value: Optional[Decimal] = Field(default=Decimal(1), gt=0)

    id: Optional[int] = None
    details: Optional[str] = ""
    amount: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    norm: Optional[Norm] = Norm()
    modifiers: Optional[list[ModifiersRequest]] = []
    purchase_price: Decimal = Field(Decimal(0))

    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def get_type_name(self) -> id:
        pass


class IRequests(ABC, BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    id: Optional[int] = Field(None)
    client: Optional[int] = Field(None)
    serial: Optional[str] = Field(None)
    type: Any = Field(...)
    products: list[IProductsRequest] = Field(..., min_length=1)
    discount: Optional[Discount] = None
    details: Optional[str] = ""
    all_discounted: Optional[bool] = Field(default=False)
    credit_card: Optional[bool] = False
    promotion: Optional[int] = None
    kind: REQUEST_KIND = REQUEST_KIND.NORMAL

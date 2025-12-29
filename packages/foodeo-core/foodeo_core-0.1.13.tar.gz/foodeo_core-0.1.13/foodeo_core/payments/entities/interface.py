from decimal import Decimal
from typing import Optional, Any

from pydantic import BaseModel


class BasePaymentData(BaseModel):
    logged_user: int
    user: int
    credit_card: Optional[bool] = False
    payed_by: Optional[str] = "foodeo"
    payment_method: Any
    tip: Optional[Decimal] = Decimal(0)


class PaymentByPriceData(BaseModel):
    command: Any
    price: Decimal
    total_price: Decimal
    credit_card: bool
    user: int
    logged_user: int
    payment_method: Any


class ProductsInPayment(BaseModel):
    id: str | int
    qty_payed: int
    total_price: Decimal


class PaymentByProductsData(BaseModel):
    command: Any
    total_price: Decimal
    table_price: Optional[Decimal | None] = None
    credit_card: bool
    user: int
    logged_user: int
    products: list[ProductsInPayment]
    identifier: Optional[str] = ""
    partial_request_price: Optional[Decimal | None] = None
    type: Optional[str | None] = None
    request_products: Optional[list[ProductsInPayment] | None] = None
    payment_method: Any


class PaymentByAllRequest(BasePaymentData):
    request: Any


class PaymentByAllCommand(BasePaymentData):
    command: Any
    dataphone: Optional[Any] = None
    cashier: Optional[Any] = None

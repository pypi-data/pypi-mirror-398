from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from foodeo_core.printers.entities.enums import CURRENCIES, PrinterWidth, FontStyle, FISKALY_INVOICE_TYPE, \
    CashierCloseType


class FontSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    size: Optional[int] = None
    style: Optional[FontStyle] = None


class PrintSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    show_header: Optional[bool] = None
    show_price_per_unit: Optional[bool] = None
    show_total_price: Optional[bool] = None
    header_font: Optional[FontSettings] = None
    details_font: Optional[FontSettings] = None
    total_font: Optional[FontSettings] = None


class Option(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    qty: Optional[int] = None


class Products(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    qty: Optional[int] = None
    details: Optional[str] = None
    price: Optional[float] = None
    unitary_price: Optional[float] = None
    option: Optional[list[Option]] = None


class ProductsGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group: Optional[str] = None
    products: Optional[list[Products]] = None


class HeaderData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    worker_name: Optional[str] = None
    company_reason: Optional[str] = None
    company_name: Optional[str] = None
    company_dni: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None


class IvaData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    impo: Optional[float] = None
    Base_: Optional[float] = Field(default=None, alias="Base")  # "Base" es alias del JSON
    iva: Optional[float] = None


class Discount(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Optional[str] = None
    value: Optional[float] = None
    total: Optional[float] = None


class FiskalyData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fiskaly_invoice_url: Optional[str] = None
    fiskaly_invoice_text: Optional[str] = None
    fiskaly_invoice_type: Optional[FISKALY_INVOICE_TYPE] = None


class Data(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    table_name: Optional[str] = None
    serial: Optional[str] = None
    is_invoice: Optional[bool] = None
    created_at: Optional[datetime] = None
    headerData: Optional[HeaderData] = None
    qr: Optional[str] = None
    is_active: Optional[bool] = None
    credit_card: Optional[bool] = None
    products: Optional[list[Products]] = None
    products_groups: Optional[list[ProductsGroup]] = None
    total: Optional[float] = None
    tip_amount: Optional[float] = None
    details: Optional[str] = None
    ticket_text: Optional[str] = None
    ivaData: Optional[IvaData] = None
    discount: Optional[Discount] = None
    price_per_person: Optional[float] = None
    command_guests: Optional[int] = None
    payed_with: Optional[str] = None
    fiskalyData: Optional[FiskalyData] = None


class CashierData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    port: Optional[int] = None
    pulse: Optional[int] = None


class CashierCloseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    close_type: Optional[CashierCloseType] = None
    serial: Optional[str] = None
    social_reason: Optional[str] = None
    nif_cif: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[str] = None
    base_imp: Optional[float] = None
    cash_register: Optional[float] = None
    card_bank: Optional[float] = None
    card_unbalance: Optional[float] = None
    initial_import: Optional[float] = None
    total_barra: Optional[float] = None
    total_barra_credit_card: Optional[float] = None
    total_recoger: Optional[float] = None
    total_recoger_credit_card: Optional[float] = None
    total_domicilio: Optional[float] = None
    total_domicilio_credit_card: Optional[float] = None
    total_general_domicilio: Optional[float] = None
    total_local: Optional[float] = None
    total_local_credit_card: Optional[float] = None
    total_cash: Optional[float] = None
    total_credit_card: Optional[float] = None
    total_cash_box: Optional[float] = None
    total_discounted: Optional[float] = None
    total_economic_subscription: Optional[float] = None
    total_imp: Optional[float] = None
    total_general: Optional[float] = None
    total_general_sales: Optional[float] = None
    total_general_recoger: Optional[float] = None
    total_general_barra: Optional[float] = None
    total_general_local: Optional[float] = None
    total_general_tips: Optional[float] = None
    total_general_expenses: Optional[float] = None
    total_expenses_credit_card: Optional[float] = None
    total_expenses_cash: Optional[float] = None
    unbalance: Optional[float] = None
    ivaData: Optional[IvaData] = None


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Optional[int] = None
    printer: Optional[str] = None
    printer_qty: Optional[int] = None
    printer_width: Optional[PrinterWidth] = None
    currency: Optional[CURRENCIES] = None
    data: Optional[Data] = None
    cashierData: Optional[CashierData] = None
    printSettings: Optional[PrintSettings] = None
    cashierCloseData: Optional[CashierCloseData] = None


class MessageWraper(BaseModel):  # Se respeta el nombre original (con una 'p')
    model_config = ConfigDict(populate_by_name=True)

    message: Optional[list[Message]] = None


# Placeholders para tipos no definidos en el snippet original
class TransactionStatusData(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    # Acepta cualquier payload que venga de CashMatic

from typing import List, Optional

from pydantic import BaseModel


class Category(BaseModel):
    """Categoría del sistema"""
    type: str


class System(BaseModel):
    """Sistema de impuestos"""
    type: str
    category: Category


class Item(BaseModel):
    """Ítem de la factura"""
    text: str
    quantity: str
    unit_amount: str
    full_amount: str
    system: System


class Content(BaseModel):
    """Contenido de la factura"""
    type: str
    number: str
    series: str
    text: str
    full_amount: str
    items: List[Item]

class CorrectContent(BaseModel):
    """Contenido de la factura de corrección"""
    type: str
    id: str
    invoice: Content
    method: str


class InvoiceData(BaseModel):
    """Datos de la factura"""
    content: Content
    metadata: Optional[dict] = None


class CorrectiveInvoiceData(BaseModel):
    """Datos de la factura"""
    content: CorrectContent
    metadata: Optional[dict] = None

from enum import Enum


class PrinterWidth(str, Enum):
    mm80 = "mm80"
    mm58 = "mm58"


class CURRENCIES(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    JPY = "JPY"
    MXN = "MXN"
    BLR = "BLR"
    DOP = "DOP"


class CashierCloseType(str, Enum):
    close_shift = "close_shift"
    close_box = "close_box"


class FISKALY_INVOICE_TYPE(str, Enum):
    VERIFACTU = "VERIFACTU"
    TICKETBAI = "TICKETBAI"


class CashmaticOps(str, Enum):
    StartPayment = "StartPayment"
    CancelPayment = "CancelPayment"


# Mapas razonables para tipos System.Drawing
class FontStyle(str, Enum):
    Regular = "Regular"
    Bold = "Bold"
    Italic = "Italic"
    Underline = "Underline"
    Strikeout = "Strikeout"


class StringAlignment(str, Enum):
    Near = "Near"
    Center = "Center"
    Far = "Far"

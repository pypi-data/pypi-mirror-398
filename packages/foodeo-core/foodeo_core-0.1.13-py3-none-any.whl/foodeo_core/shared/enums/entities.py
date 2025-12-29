from enum import Enum


class DiscountEnum(str, Enum):
    percentage = "percent"
    numeric = "number"
    empty = ""


class DiscountPromotionEnum(str, Enum):
    NUMBER = "number"
    PERCENT = "percent"


class RequestEnum(str, Enum):
    domicile = "domicilio"
    local = "local"
    pickup = "recoger"
    barra = "barra"
    kiosko = "kiosko"


class CommandEnum(str, Enum):
    domicile = "domicile"
    local = "local"
    pickup = "recoger"
    barra = "barra"
    kiosko = "kiosko"


class StatusEnum(str, Enum):
    draft = "borrador"
    requested = "solicitado"
    closed = "cerrado"
    canceled = "cancelado"
    invalidated = "invalidado"
    terminated = "terminado"
    prepaid = "prepago"


class CommandStatusEnum(str, Enum):
    pre_payed = "prepago"
    draft = "borrador"
    open = 'abierta'
    payed = 'pagada'
    parcial = 'parcial'
    canceled = "cancelada"
    invalidated = "invalidada"
    terminated = "terminada"
    deleted = "eliminada"
    blocked = "bloqueada"


class FromClientEnum(str, Enum):
    apk = "apk"
    web = "web"
    web_sales = "web_sales"
    kiosko = "kiosko"


class UnitEnum(str, Enum):
    quantity = "quantity"
    volume = "volume"
    weight = "weight"


class UnitOfMeasureEnum(str, Enum):
    cl = "cl"
    dl = "dl"
    L = "L"
    oz = "oz"
    lb = "lb"
    kg = "kg"
    g = "g"
    ml = "ml"
    ud = "ud"
    empty = ""


class TipOptionsEnum(str, Enum):
    five_percent = '5%'
    ten_percent = '10%'
    other = 'other'
    no_tip = 'no_tip'


class PaymentType(str, Enum):
    price = "price"
    product = "product"


class FromClient(str, Enum):
    web = "web"
    apk = "apk"
    web_sales = "web_sales"
    kiosko = "kiosko"


class PaymentStatus(str, Enum):
    pending = "pending"
    partial = "partial"
    draft = "draft"
    cancelled = "cancelled"
    completed = "completed"
    finished = "finished"


class PAYED_WITH_ENUM(str, Enum):
    credit_card = 'credit_card'
    cash = 'cash'
    split = 'split'


class PRINTER_WIDTH_OPTIONS(str, Enum):
    PINTER_WIDTH_80 = '0'
    PINTER_WIDTH_58 = '1'


class TYPE_ALERT_NOTIFICATION(str, Enum):
    ALERT = 'alert'
    BLOCKED = 'blocked'


class COLOR_ALERT_NOTIFICATION(str, Enum):
    INFO = 'info'
    SUCCESS = 'success'
    ERROR = 'error'


class FISKALY_COUNTRY_CODES(str, Enum):
    ESP = 'info'
    AND = 'success'


class FISKALY_TERRITORIES(str, Enum):
    ARABA = 'ARABA'
    BIZKAIA = 'BIZKAIA'
    GIPUZKOA = 'GIPUZKOA'
    NAVARRE = 'NAVARRE'
    CANARY_ISLANDS = 'CANARY_ISLANDS'
    CEUTA = 'CEUTA'
    MELILLA = 'MELILLA'
    SPAIN_OTHER = 'SPAIN_OTHER'


class PAYMENTS_SHAPE(str, Enum):
    CARD = 'card'
    CASH = 'cash'
    BOTH = 'both'


class ReservationsStatusEnum(str, Enum):
    ACCEPTED = "accepted"
    DENIED = "denied"
    NEW = "new"


class DaysChoicesEnum(str, Enum):
    MONDAY = 'Monday'
    TUESDAY = 'Tuesday'
    WEDNESDAY = 'Wednesday'
    THURSDAY = 'Thursday'
    FRIDAY = 'Friday'
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'


class ExpensesStatusEnum(str, Enum):
    created = '0'
    processed = '1'


class FiskalyCountryCodes(str, Enum):
    AND = 'AND'
    ESP = 'ESP'


class FiskalyTerritories(str, Enum):
    ARABA = 'ARABA'
    BIZKAIA = 'BIZKAIA'
    GIPUZKOA = 'GIPUZKOA'
    NAVARRE = 'NAVARRE'
    CANARY_ISLANDS = 'CANARY_ISLANDS'
    CEUTA = 'CEUTA'
    MELILLA = 'MELILLA'
    SPAIN_OTHER = 'SPAIN_OTHER'

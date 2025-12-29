from decimal import Decimal

from foodeo_core.settings.abstractions.isettings_manager import ISettingsManager


class CalculateIVA:
    def __init__(self, settings: ISettingsManager, tenant=None):
        self.settings: ISettingsManager = settings
        self.tenant = tenant

    def get_impo(self, request_price: Decimal, price_domicile=0):
        iva: Decimal = self.settings.get_global_settings(using=self.tenant).iva
        total: Decimal = request_price + price_domicile
        base: Decimal = (total / (1 + iva / 100)).quantize(Decimal('.01'))
        return str(total - base)

    def get_base(self, request_price: Decimal, price_domicile=0):
        iva: Decimal = self.settings.get_global_settings(using=self.tenant).iva
        total: Decimal = request_price
        if price_domicile != 0:
            total += price_domicile
        base: Decimal = (total / (1 + iva / 100)).quantize(Decimal('.01'))
        return str(base)

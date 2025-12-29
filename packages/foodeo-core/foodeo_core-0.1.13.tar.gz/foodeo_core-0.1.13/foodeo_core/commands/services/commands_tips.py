from decimal import Decimal

from foodeo_core.commands.entities.modifiers import TIPS_OPTIONS, COMMANDS_TYPES
from foodeo_core.shared.entities.commands import TipCalculation


class CommandTipCalculator:

    def calculate_tip(self, tip_model: TipCalculation) -> Decimal:
        price = self._get_total_price(tip_model)

        match tip_model.tip_option:
            case TIPS_OPTIONS.FIVE_PERCENT:
                return self._round(price * Decimal('0.05'))
            case TIPS_OPTIONS.TEN_PERCENT:
                return self._round(price * Decimal('0.10'))
            case TIPS_OPTIONS.OTHER:
                return self._round(tip_model.tip_amount)
            case _:
                return Decimal('0.00')

    def _round(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal('.01'))

    def _get_total_price(self, tip_model: TipCalculation) -> Decimal:
        base_price = tip_model.price
        if tip_model.type == COMMANDS_TYPES.DOMICILE and tip_model.domicile_price:
            base_price += tip_model.domicile_price
        return base_price.quantize(Decimal('.01'))

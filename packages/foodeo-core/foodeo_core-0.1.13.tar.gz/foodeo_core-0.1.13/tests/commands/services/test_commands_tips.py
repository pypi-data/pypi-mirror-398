import unittest
from decimal import Decimal

from foodeo_core.commands.entities.modifiers import COMMANDS_TYPES, TIPS_OPTIONS
from foodeo_core.commands.services.commands_tips import CommandTipCalculator
from foodeo_core.shared.entities.commands import TipCalculation


class TestCommandTipCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = CommandTipCalculator()

    def test_percentage_tip_options(self) -> None:
        cases = [
            {
                "name": "five_percent_local",
                "tip_option": TIPS_OPTIONS.FIVE_PERCENT.value,
                "price": Decimal("100.00"),
                "command_type": COMMANDS_TYPES.LOCAL.value,
                "domicile_price": None,
                "expected_tip": Decimal("5.00"),
            },
            {
                "name": "ten_percent_includes_domicile",
                "tip_option": TIPS_OPTIONS.TEN_PERCENT.value,
                "price": Decimal("12.00"),
                "command_type": COMMANDS_TYPES.DOMICILE.value,
                "domicile_price": Decimal("3.50"),
                "expected_tip": Decimal("1.55"),  # (12.00 + 3.50) * 10%
            },
            {
                "name": "ten_percent_ignores_domicile_for_local",
                "tip_option": TIPS_OPTIONS.TEN_PERCENT.value,
                "price": Decimal("40.00"),
                "command_type": COMMANDS_TYPES.LOCAL.value,
                "domicile_price": Decimal("5.00"),
                "expected_tip": Decimal("4.00"),
            },
        ]

        for case in cases:
            with self.subTest(case=case["name"]):
                tip_model = TipCalculation(
                    price=case["price"],
                    type=case["command_type"],
                    domicile_price=case["domicile_price"],
                    tip_option=case["tip_option"],
                )
                tip_value = self.calculator.calculate_tip(tip_model)

                self.assertEqual(tip_value, case["expected_tip"])

    def test_other_tip_uses_given_amount_and_rounds(self) -> None:
        tip_model = TipCalculation(
            price=Decimal("10.00"),
            type=COMMANDS_TYPES.BARRA.value,
            tip_option=TIPS_OPTIONS.OTHER.value,
            tip_amount=Decimal("3.456"),
        )

        self.assertEqual(self.calculator.calculate_tip(tip_model), Decimal("3.46"))

    def test_domicile_without_fee_uses_base_price_only(self) -> None:
        tip_model = TipCalculation(
            price=Decimal("18.40"),
            type=COMMANDS_TYPES.DOMICILE.value,
            domicile_price=None,
            tip_option=TIPS_OPTIONS.FIVE_PERCENT.value,
        )

        self.assertEqual(self.calculator.calculate_tip(tip_model), Decimal("0.92"))

    def test_total_price_is_quantized_before_percentage(self) -> None:
        tip_model = TipCalculation(
            price=Decimal("10.129"),
            type=COMMANDS_TYPES.DOMICILE.value,
            domicile_price=Decimal("0"),
            tip_option=TIPS_OPTIONS.TEN_PERCENT.value,
        )

        # price should be rounded to 10.13 before applying 10%
        self.assertEqual(self.calculator.calculate_tip(tip_model), Decimal("1.01"))

    def test_no_tip_returns_zero(self) -> None:
        tip_model = TipCalculation(
            price=Decimal("25.00"),
            type=COMMANDS_TYPES.KIOSKO.value,
            tip_option=TIPS_OPTIONS.NO_TIP.value,
            domicile_price=Decimal("5.00"),
        )

        self.assertEqual(self.calculator.calculate_tip(tip_model), Decimal("0.00"))

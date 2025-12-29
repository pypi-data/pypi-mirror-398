import unittest
from decimal import Decimal

from foodeo_core.commands.services.price_and_discount import PriceAndDiscountService
from foodeo_core.shared.entities import Discount
from foodeo_core.shared.entities.irequests import ModifiersRequest
from foodeo_core.shared.entities.requests import Request
from foodeo_core.shared.entities.requests_items import ProductInRequest
from foodeo_core.shared.enums import DiscountEnum, FromClientEnum, RequestEnum


class TestPriceAndDiscountService(unittest.TestCase):
    def _build_request(
            self,
            products: list[ProductInRequest],
            discount: Discount | None = None,
            request_type: RequestEnum = RequestEnum.local,
    ) -> Request:
        return Request(
            type=request_type,
            from_client=FromClientEnum.apk,
            products=products,
            discount=discount,
        )

    def test_get_price_and_discount_without_discount(self) -> None:
        modifiers = [
            ModifiersRequest(modifiers_id=1, options_id=1, importe=Decimal("1.50")),
            ModifiersRequest(
                modifiers_id=1,
                options_id=2,
                options_child_id=7,
                importe=Decimal("0.75"),
                importe_child=Decimal("0.25"),
            ),
        ]
        product = ProductInRequest(
            name="Burger",
            qty=2,
            price=Decimal("10.00"),
            modifiers=modifiers,
            is_discounted=False,
        )
        request = self._build_request(products=[product])

        original_price, request_price = PriceAndDiscountService.get_price_and_discount(request)

        self.assertEqual(original_price, Decimal("25.00"))
        self.assertEqual(request_price, Decimal("25.00"))
        self.assertEqual(product.total_price, Decimal("25.00"))
        self.assertEqual(product.unit_price, Decimal("10.00"))

    def test_options_price_deduplicates_parent_when_child_present(self) -> None:
        modifiers = [
            ModifiersRequest(
                modifiers_id=1,
                options_id=2,
                options_child_id=1,
                importe=Decimal("1.00"),
                importe_child=Decimal("0.50"),
            ),
            ModifiersRequest(
                modifiers_id=1,
                options_id=2,
                options_child_id=2,
                importe=Decimal("1.00"),
                importe_child=Decimal("0.25"),
            ),
        ]

        total = PriceAndDiscountService.get_options_price(modifiers)

        # Adds importe_child for each child, but the parent importe only once
        self.assertEqual(total, Decimal("1.75"))

    def test_global_percentage_discount(self) -> None:
        product = ProductInRequest(name="Pizza", qty=1, price=Decimal("50.00"), is_discounted=True)
        discount = Discount(type=DiscountEnum.percentage, value=10, global_discount=True)
        request = self._build_request(products=[product], discount=discount)

        original_price, request_price = PriceAndDiscountService.get_price_and_discount(request)

        self.assertEqual(original_price, Decimal("50.00"))
        self.assertEqual(request_price, Decimal("45.00"))

    def test_percentage_discount_only_affects_discounted_products(self) -> None:
        discounted = ProductInRequest(name="Pasta", qty=2, price=Decimal("10.00"), is_discounted=True, modifiers=[])
        not_discounted = ProductInRequest(name="Soda", qty=1, price=Decimal("5.00"), is_discounted=False, modifiers=[])
        discount = Discount(type=DiscountEnum.percentage, value=50, global_discount=False)
        request = self._build_request(products=[discounted, not_discounted], discount=discount)

        original_price, request_price = PriceAndDiscountService.get_price_and_discount(request)

        self.assertEqual(original_price, Decimal("25.00"))
        self.assertEqual(request_price, Decimal("15.00"))  # Only the discounted product gets 50% off
        self.assertEqual(discounted.total_price, Decimal("10.00"))
        self.assertEqual(not_discounted.total_price, Decimal("5.00"))

    def test_numeric_discount_applies_only_to_discounted_products(self) -> None:
        discounted_product = ProductInRequest(
            name="Salad",
            qty=1,
            price=Decimal("20.00"),
            is_discounted=True,
            modifiers=[],
        )
        non_discounted_product = ProductInRequest(
            name="Drink",
            qty=2,
            price=Decimal("5.00"),
            is_discounted=False,
            modifiers=[],
        )
        discount = Discount(type=DiscountEnum.numeric, value=Decimal("3.00"), global_discount=False)
        request = self._build_request(products=[discounted_product, non_discounted_product], discount=discount)

        original_price, request_price = PriceAndDiscountService.get_price_and_discount(request)

        self.assertEqual(original_price, Decimal("30.00"))
        self.assertEqual(request_price, Decimal("27.00"))
        self.assertEqual(discounted_product.total_price, Decimal("17.00"))  # 20 - 3 numeric discount
        self.assertEqual(non_discounted_product.total_price, Decimal("10.00"))

    def test_discount_cannot_make_total_negative(self) -> None:
        product = ProductInRequest(name="Snack", qty=1, price=Decimal("5.00"), is_discounted=True, modifiers=[])
        discount = Discount(type=DiscountEnum.numeric, value=Decimal("10.00"), global_discount=True)
        request = self._build_request(products=[product], discount=discount)

        original_price, request_price = PriceAndDiscountService.get_price_and_discount(request)

        self.assertEqual(original_price, Decimal("5.00"))
        self.assertEqual(request_price, Decimal("0.00"))
        self.assertEqual(product.total_price, Decimal("-5.00"))

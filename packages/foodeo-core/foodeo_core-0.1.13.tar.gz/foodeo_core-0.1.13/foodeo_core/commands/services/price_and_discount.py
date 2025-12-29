from decimal import Decimal

from foodeo_core.shared.entities import Discount
from foodeo_core.shared.entities.irequests import IRequests, IProductsRequest, IModifierRequest
from foodeo_core.shared.enums import DiscountEnum
from foodeo_core.shared.helpers import normalize


class PriceAndDiscountService:
    discount: Discount = None

    @classmethod
    def get_price_and_discount(cls, request: IRequests) -> tuple[Decimal, Decimal]:
        cls.discount = request.discount

        request_price: Decimal = cls.get_products_price(request.products)
        original_price: Decimal = request_price

        if request.discount:
            if request.discount.global_discount:
                discount_value = cls.get_discount_value(original_price, request.discount)
            else:
                product_price_without_discount = cls.get_products_price(request.products, True)
                discount_value = cls.get_discount_value(product_price_without_discount, request.discount)

            request_price -= discount_value
        request_price = 0 if request_price < 0 else request_price

        original_price = normalize(original_price)
        request_price = normalize(request_price)
        return original_price, request_price

    @classmethod
    def get_products_price(cls, products: list[IProductsRequest], is_discounted: bool = False) -> Decimal:
        request_price: Decimal = Decimal(0)

        for product in products:
            if is_discounted and not product.is_discounted:
                continue

            unit_price: Decimal = product.price + cls.get_options_price(product.modifiers)

            request_price += cls.get_price(unit_price, product.qty)

            # Update other price types
            product.amount = normalize(cls.get_price(product.price, product.qty))

            product.total_price = cls.get_price(unit_price, product.qty)
            if product.is_discounted:
                product.total_price -= cls.get_discount_value(product.total_price, cls.discount)

            product.unit_price = normalize(product.amount / product.qty)

        return request_price

    @classmethod
    def get_options_price(cls, modifiers: list[IModifierRequest]) -> Decimal:
        total_options_price: Decimal = Decimal(0)
        list_modifiers_options: list[str] = []
        for modifier in modifiers:
            key = str(modifier.modifiers_id) + str(modifier.options_id)
            if not modifier.options_child_id:
                total_options_price += modifier.importe
            else:
                total_options_price += modifier.importe_child
                if key not in list_modifiers_options:
                    total_options_price += modifier.importe
                    list_modifiers_options.append(key)

        return total_options_price

    @classmethod
    def get_discount_value(cls, price: Decimal, discount: Discount) -> Decimal:
        discount_value: Decimal = price
        match discount.type:
            case DiscountEnum.numeric:
                discount_value = Decimal(discount.value)
            case DiscountEnum.percentage:
                discount_value = (price * Decimal(discount.value)) / Decimal(100)

        return discount_value

    @classmethod
    def get_price(cls, price: Decimal, qty: int) -> Decimal:
        return Decimal(qty) * Decimal(price)

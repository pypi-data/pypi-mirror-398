from enum import StrEnum


class SetupProductsEnum(StrEnum):
    with_products = "with_products"
    with_many_products = "with_many_products"


class SetupDiscountsEnum(StrEnum):
    with_percentage_all_discounted = "with_percentage_all_discounted"
    with_numeric_all_discounted = "with_numeric_all_discounted"
    with_percentage_discounted = "with_percentage_discounted"
    without_discounted = "without_discounted"

from decimal import Decimal


def round_out_money(amount: Decimal) -> Decimal:
    return Decimal(amount).quantize(Decimal('.00001'))


def truncated(amount: Decimal, decimal_places: int = 2) -> Decimal:
    structure = "{0:.%sf}" % decimal_places
    return Decimal(structure.format(amount))


def is_equivalent(amount: Decimal, other_amount: Decimal, tryhold: Decimal = Decimal(0.01)) -> bool:
    amount, other_amount = truncated(amount), truncated(other_amount)
    return abs(amount - other_amount) <= tryhold


def normalize(amount: Decimal):
    amount = round_out_money(amount)
    amount = truncated(amount)

    return amount

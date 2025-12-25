from decimal import Decimal, ROUND_HALF_EVEN

_bound = Decimal('0.0001')

def boundValue(value: float) -> float:
    # bound to 4 places with as tight rounding as possible
    return float(Decimal(value).quantize(exp = _bound, rounding = ROUND_HALF_EVEN))
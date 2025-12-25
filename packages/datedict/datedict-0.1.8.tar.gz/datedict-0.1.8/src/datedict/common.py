from decimal import Decimal
from typing import Union

Decimable = Union[Decimal, str, int, float, None]

ZERO = Decimal("0")
ONE = Decimal("1")
NAN = Decimal("NaN")


def to_decimal(x: Decimable) -> Decimal:
    if x is None:
        return Decimal("NaN")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, str)):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(str(x))
